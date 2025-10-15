"""consumption_principals_columns_and_schema

Revision ID: 89c3bfe59cad
Revises: 77c3f1b2bec8
Create Date: 2025-05-08 14:31:30.098503

"""

import datetime
from typing import List

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, orm, Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

from dataall.base.db import utils
from dataall.base.utils.consumption_principal_utils import EnvironmentIAMPrincipalType

# revision identifiers, used by Alembic.
revision = '89c3bfe59cad'
down_revision = '77c3f1b2bec8'
branch_labels = None
depends_on = None

Base = declarative_base()


class ConsumptionPrincipal(Base):
    __tablename__ = 'consumptionprincipals'
    consumptionPrincipalUri = Column(String, primary_key=True, default=utils.uuid('group'))
    consumptionPrincipalName = Column(String, nullable=False)
    environmentUri = Column(String, nullable=False)
    groupUri = Column(String, nullable=False)
    IAMPrincipalName = Column(String, nullable=False)
    IAMPrincipalArn = Column(String, nullable=False)
    dataallManaged = Column(String, nullable=False)
    created = Column(DateTime, default=datetime.datetime.now)
    updated = Column(DateTime, onupdate=datetime.datetime.now)
    deleted = Column(DateTime)
    consumptionPrincipalType = Column(String, nullable=False)


def get_session():
    bind = op.get_bind()
    session = orm.Session(bind=bind)
    return session


def column_exists(table_name, column_name):
    bind = op.get_context().bind
    insp = inspect(bind)
    columns = insp.get_columns(table_name)
    return any(c['name'] == column_name for c in columns)


def table_exists(table_name):
    bind = op.get_context().bind
    insp = inspect(bind)
    return table_name in insp.get_table_names()


def upgrade():
    op.rename_table('consumptionrole', 'consumptionprincipals')
    op.alter_column(
        table_name='consumptionprincipals', column_name='consumptionRoleUri', new_column_name='consumptionPrincipalUri'
    )
    op.alter_column(
        table_name='consumptionprincipals',
        column_name='consumptionRoleName',
        new_column_name='consumptionPrincipalName',
    )
    op.alter_column(table_name='consumptionprincipals', column_name='IAMRoleName', new_column_name='IAMPrincipalName')
    op.alter_column(table_name='consumptionprincipals', column_name='IAMRoleArn', new_column_name='IAMPrincipalArn')

    consumption_type_enum = sa.Enum(EnvironmentIAMPrincipalType, name='consumption_principal_type')
    consumption_type_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        table_name='consumptionprincipals',
        column=sa.Column(
            'consumptionPrincipalType',
            sa.Enum(EnvironmentIAMPrincipalType, name='consumption_principal_type'),
            nullable=True,
        ),
    )

    session = get_session()

    # For all consumption roles, set the consumptionPrincipalType column value to ConsumptionPrincipalType.ROLE.value
    consumption_roles: List[ConsumptionPrincipal] = session.query(ConsumptionPrincipal).all()
    for consumption_role in consumption_roles:
        consumption_role.consumptionPrincipalType = EnvironmentIAMPrincipalType.ROLE.value
    session.add_all(consumption_roles)
    session.commit()

    op.alter_column(table_name='consumptionprincipals', column_name='consumptionPrincipalType', nullable=False)

    op.alter_column(
        table_name='share_object', column_name='principalRoleName', new_column_name='principalName'
    ) if not column_exists('share_object', 'principalName') else None


def downgrade():
    # Check if the name of the table has changes .
    if table_exists('consumptionprincipals'):
        op.rename_table('consumptionprincipals', 'consumptionrole')
        op.alter_column(
            table_name='consumptionrole', new_column_name='consumptionRoleUri', column_name='consumptionPrincipalUri'
        ) if column_exists('consumptionrole', 'consumptionPrincipalUri') else None
        op.alter_column(
            table_name='consumptionrole', new_column_name='consumptionRoleName', column_name='consumptionPrincipalName'
        ) if column_exists('consumptionrole', 'consumptionPrincipalName') else None
        op.alter_column(
            table_name='consumptionrole', new_column_name='IAMRoleName', column_name='IAMPrincipalName'
        ) if column_exists('consumptionrole', 'IAMPrincipalName') else None
        op.alter_column(
            table_name='consumptionrole', new_column_name='IAMRoleArn', column_name='IAMPrincipalArn'
        ) if column_exists('consumptionrole', 'IAMPrincipalArn') else None
        op.drop_column(table_name='consumptionrole', column_name='consumptionPrincipalType') if column_exists(
            'consumptionrole', 'consumptionPrincipalType'
        ) else None
        op.execute('DROP TYPE IF EXISTS consumption_principal_type')

        op.alter_column(
            table_name='share_object', column_name='principalName', new_column_name='principalRoleName'
        ) if column_exists('share_object', 'principalName') else None
