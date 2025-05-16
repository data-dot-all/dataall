"""Consumption role schema change and backfilling

Revision ID: 77c3f1b2bec8
Revises: af2e1362d4cb
Create Date: 2025-02-05 11:05:55.782419

"""
import datetime
from typing import List, Dict

from alembic import op
import sqlalchemy as sa
from sqlalchemy import orm, Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

from dataall.base.db import utils
from dataall.core.environment.db.environment_enums import PolicyManagementOptions
from dataall.core.environment.db.environment_models import ConsumptionPrincipal

# revision identifiers, used by Alembic.
revision = '77c3f1b2bec8'
down_revision = '5c5e78526cae'
branch_labels = None
depends_on = None

Base = declarative_base()

def get_session():
    bind = op.get_bind()
    session = orm.Session(bind=bind)
    return session

class ConsumptionRole(Base):
    __tablename__ = 'consumptionrole'
    consumptionRoleUri = Column(String, primary_key=True, default=utils.uuid('group'))
    consumptionRoleName = Column(String, nullable=False)
    environmentUri = Column(String, nullable=False)
    groupUri = Column(String, nullable=False)
    IAMRoleName = Column(String, nullable=False)
    IAMRoleArn = Column(String, nullable=False)
    dataallManaged = Column(String, nullable=False)
    created = Column(DateTime, default=datetime.datetime.now)
    updated = Column(DateTime, onupdate=datetime.datetime.now)
    deleted = Column(DateTime)

def upgrade():
    # Update the column type to String and also remove the DEFAULT True
    op.alter_column(
        table_name='consumptionrole',
        column_name='dataallManaged',
        nullable=False,
        existing_type=sa.Boolean(),
        type_=sa.String(),
        server_default=None,
    )

    session = get_session()

    # For all consumption roles, set the dataallManaged column value with the PolicyManagementOptions types
    consumption_roles: List[ConsumptionRole] = session.query(ConsumptionRole).all()
    for consumption_role in consumption_roles:
        if consumption_role.dataallManaged == 'true':
            consumption_role.dataallManaged = PolicyManagementOptions.FULLY_MANAGED.value
        else:
            consumption_role.dataallManaged = PolicyManagementOptions.PARTIALLY_MANAGED.value
    session.add_all(consumption_roles)
    session.commit()


def downgrade():
    session = get_session()
    consumption_roles: List[ConsumptionRole] = session.query(ConsumptionRole).all()
    # For each consumption role, get the policy management options and set value to True if FullyManaged else False
    consumption_role_policy_mgmt_map: Dict[str, str] = {
        consumption_role.consumptionRoleUri: True
        if consumption_role.dataallManaged == PolicyManagementOptions.FULLY_MANAGED.value
        else False
        for consumption_role in consumption_roles
    }

    op.drop_column(table_name='consumptionrole', column_name='dataallManaged')
    op.add_column(
        'consumptionrole',
        sa.Column('dataallManaged', sa.Boolean(), nullable=False, server_default=sa.sql.expression.true()),
    )

    # Update all the consumption.dataallManaged column with boolean values by using consumption_role_policy_mgmt_map map
    consumption_roles: List[ConsumptionRole] = session.query(ConsumptionRole).all()
    for consumption_role in consumption_roles:
        consumption_role.dataallManaged = consumption_role_policy_mgmt_map.get(
            consumption_role.consumptionRoleUri, True
        )
    session.add_all(consumption_roles)
    session.commit()
