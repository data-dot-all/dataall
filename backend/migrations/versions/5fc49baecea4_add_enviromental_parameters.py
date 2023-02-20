"""add_enviromental_parameters

Revision ID: 5fc49baecea4
Revises: d05f9a5b215e
Create Date: 2023-02-20 14:28:13.331670

"""

from alembic import op
from sqlalchemy import Boolean, Column, String, orm
from sqlalchemy.ext.declarative import declarative_base
from dataall.db.api.permission import Permission
from dataall.db import Resource


# revision identifiers, used by Alembic.
revision = '5fc49baecea4'
down_revision = 'd05f9a5b215e'
branch_labels = None
depends_on = None

Base = declarative_base()


class Environment(Resource, Base):
    __tablename__ = 'environment'
    environmentUri = Column(String, primary_key=True)

    dashboardsEnabled = Column(Boolean)
    notebooksEnabled = Column(Boolean)
    mlStudiosEnabled = Column(Boolean)
    pipelinesEnabled = Column(Boolean)
    warehousesEnabled = Column(Boolean)

def upgrade():
    """
    The script does the following migration:
        1) creation of the environment_parameters and environment_resources tables
        2) Migration xxxEnabled to the environment_parameters table
        3) Dropping the xxxEnabled columns from the environment_parameters
        4) Migration every resource allocated for the environment to the environment_resources
        5) Updates the permissions
    """
    try:
        bind = op.get_bind()
        session = orm.Session(bind=bind)
        print('Initializing permissions...')
        Permission.init_permissions(session)
        print('Permissions initialized successfully')


    except Exception as ex:
        print(f'Failed to execute the migration script due to: {ex}')




def downgrade():
    op.drop_table("environment_resources")
