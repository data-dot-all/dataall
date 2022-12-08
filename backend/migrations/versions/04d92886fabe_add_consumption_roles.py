"""add_consumption_roles

Revision ID: 04d92886fabe
Revises: d922057f0d91
Create Date: 2022-11-29 10:57:27.641565

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import orm, Column, String, Boolean, DateTime, and_
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.declarative import declarative_base

from dataall.db import api, models, permissions, utils
from dataall.db.models.Enums import ShareObjectStatus, ShareableType, PrincipalType
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '04d92886fabe'
down_revision = 'd922057f0d91'
branch_labels = None
depends_on = None

Base = declarative_base()


class EnvironmentGroup(Base):
    __tablename__ = 'environment_group_permission'
    groupUri = Column(String, primary_key=True)
    environmentUri = Column(String, primary_key=True)
    invitedBy = Column(String, nullable=True)
    environmentIAMRoleArn = Column(String, nullable=True)
    environmentIAMRoleName = Column(String, nullable=True)
    environmentIAMRoleImported = Column(Boolean, default=False)
    environmentAthenaWorkGroup = Column(String, nullable=True)
    description = Column(String, default='No description provided')
    created = Column(DateTime, default=datetime.now)
    updated = Column(DateTime, onupdate=datetime.now)
    deleted = Column(DateTime)


class ShareObject(Base):
    __tablename__ = 'share_object'
    shareUri = Column(
        String, nullable=False, primary_key=True, default=utils.uuid('share')
    )
    datasetUri = Column(String, nullable=False)
    environmentUri = Column(String)
    groupUri = Column(String)
    principalIAMRoleName = Column(String, nullable=True)
    principalId = Column(String, nullable=True)
    principalType = Column(String, nullable=True, default='Group')
    status = Column(String, nullable=False, default=ShareObjectStatus.Draft.value)
    owner = Column(String, nullable=False)
    created = Column(DateTime, default=datetime.now)
    updated = Column(DateTime, onupdate=datetime.now)
    deleted = Column(DateTime)
    confirmed = Column(Boolean, default=False)


def upgrade():
    op.create_table(
        'consumptionrole',
        sa.Column('consumptionRoleUri', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('consumptionRoleName', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('environmentUri', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('groupUri', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('IAMRoleName', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('IAMRoleArn', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column(
            'created', postgresql.TIMESTAMP(), autoincrement=False, nullable=True
        ),
        sa.Column(
            'updated', postgresql.TIMESTAMP(), autoincrement=False, nullable=True
        ),
        sa.Column(
            'deleted', postgresql.TIMESTAMP(), autoincrement=False, nullable=True
        ),
        sa.PrimaryKeyConstraint('consumptionRoleUri', name='consumptionRoleUri_pkey'),
    )

    op.add_column('share_object', sa.Column('principalIAMRoleName', sa.String(), nullable=True))
    op.add_column('share_object', sa.Column('groupUri', sa.String(), nullable=True))

    try:
        bind = op.get_bind()
        session = orm.Session(bind=bind)
        print('Back-filling share_object table...')
        shares: [ShareObject] = session.query(ShareObject).all()
        for share in shares:
            env_group: [EnvironmentGroup] = session.query(EnvironmentGroup).filter(
                (
                    and_(
                        EnvironmentGroup.groupUri == share.principalId,
                        EnvironmentGroup.environmentUri == share.environmentUri,
                    )
                )
            ).first()
            if not share.groupUri:
                share.groupUri = share.principalId
                share.principalIAMRoleName = env_group.environmentIAMRoleName
                session.commit()
        print('share_object table updated successfully')
    except Exception as e:
        print(f'Failed to backfill share_object due to: {e}')

    try:
        bind = op.get_bind()
        session = orm.Session(bind=bind)
        print('Re-Initializing permissions...')
        api.Permission.init_permissions(session)
        print('Permissions re-initialized successfully')
    except Exception as e:
        print(f'Failed to init permissions due to: {e}')
    # ### end Alembic commands ###

    try:
        bind = op.get_bind()
        session = orm.Session(bind=bind)
        print('Back-filling consumer role permissions for environments...')
        envs = api.Environment.list_all_active_environments(session=session)
        for env in envs:
            groups = api.Environment.query_all_environment_groups(
                session=session, uri=env.environmentUri, filter=None
            )
            for group in groups:
                api.ResourcePolicy.attach_resource_policy(
                    session=session,
                    resource_uri=env.environmentUri,
                    group=group.groupUri,
                    permissions=permissions.CONSUMPTION_ROLE_ALL,
                    resource_type=models.Environment.__name__,
                )
        print('Consumer Role Permissions created successfully')
    except Exception as e:
        print(f'Failed to back-fill Consumer Role permissions due to: {e}')


def downgrade():
    op.drop_table('consumptionrole')
    op.drop_column('share_object', 'principalIAMRoleName')
    op.drop_column('share_object', 'groupUri')
