"""maintenance_window_schema

Revision ID: b833ad41db68
Revises: 194608b1ff7f
Create Date: 2024-04-16 19:30:05.226603

"""

import os

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Column, String, orm
from sqlalchemy.ext.declarative import declarative_base

from dataall.base.db import get_engine, has_table

# revision identifiers, used by Alembic.
revision = 'b833ad41db68'
down_revision = '458572580709'
branch_labels = None
depends_on = None

Base = declarative_base()


class Maintenance(Base):
    __tablename__ = 'maintenance'
    status = Column(String, nullable=False, primary_key=True)
    mode = Column(String, default='', nullable=True)


def upgrade():
    # Upgrade scripts does the following :
    # 1. Creates the maintenance table with two columns : status and mode
    # 2. Creates a single record in maintenance table with status : INACTIVE and mode: '' ( Blank )
    try:
        envname = os.getenv('envname', 'local')
        print('ENVNAME', envname)
        engine = get_engine(envname=envname).engine

        bind = op.get_bind()
        session = orm.Session(bind=bind)

        # Create the maintenance table
        if not has_table('maintenance', engine):
            print('Creating maintenance table')

            op.create_table(
                'maintenance',
                sa.Column('status', sa.String(), nullable=False, primary_key=True),
                sa.Column('mode', sa.String(), nullable=True, default=''),
            )

            maintenance_record: [Maintenance] = Maintenance(status='INACTIVE', mode='')
            session.add(maintenance_record)
        print('Commiting single row to the maintenance table')
        session.commit()

    except Exception as e:
        print('Failed to create migration for maintenance table')
        raise e


def downgrade():
    # Script for deleting the maintenance table
    try:
        envname = os.getenv('envname', 'local')
        print('ENVNAME', envname)
        engine = get_engine(envname=envname).engine
        print('Starting downgrade of maintenance')
        if has_table('maintenance', engine=engine):
            print('Dropping table maintenance')
            op.drop_table('maintenance')
    except Exception as e:
        print('Failed to downgrade maintenance table')
        raise e
