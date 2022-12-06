"""_release_deleteme

Revision ID: eb2a6250c50a
Revises: 04d92886fabe
Create Date: 2022-12-06 13:37:39.008251

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import orm, Column, String, Boolean, DateTime, and_
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.declarative import declarative_base

from dataall.db import utils, Resource
from dataall.db.models.Enums import ShareObjectStatus, ShareableType, PrincipalType
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'eb2a6250c50a'
down_revision = '04d92886fabe'
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
    op.drop_table('consumptionrole')
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
        print('Updating share_object table...')
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
        print(f'Failed to init permissions due to: {e}')


def downgrade():
    op.drop_table('consumptionrole')
    op.drop_column('share_object', 'principalIAMRoleName')
    op.drop_column('share_object', 'groupUri')