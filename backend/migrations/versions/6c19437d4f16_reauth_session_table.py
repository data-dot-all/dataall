"""reauth_session_table

Revision ID: 6c19437d4f16
Revises: 917b923f74bd
Create Date: 2023-09-19 12:54:04.711554

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '6c19437d4f16'
down_revision = '917b923f74bd'
branch_labels = None
depends_on = None


def upgrade():
    """
    The script does the following migration:
        1) Creates auth_session table
    """
    try:
        print("Creating Auth Sessions Table...")
        op.create_table(
            'auth_session',
            sa.Column('sessionId', sa.VARCHAR(), autoincrement=False, nullable=False),
            sa.Column('clientId', sa.VARCHAR(), autoincrement=False, nullable=False),
            sa.Column('referrerUrl', sa.VARCHAR(), autoincrement=False, nullable=False),
            sa.Column('stepUpStatus', sa.VARCHAR(), autoincrement=False, nullable=False),
            sa.Column('token', sa.VARCHAR(), autoincrement=False, nullable=False),
            sa.Column('ttl', sa.VARCHAR(), autoincrement=False, nullable=False),
            sa.Column('username', sa.VARCHAR(), autoincrement=False, nullable=False),
            sa.Column(
                'created', postgresql.TIMESTAMP(), autoincrement=False, nullable=True
            ),
            sa.Column(
                'updated', postgresql.TIMESTAMP(), autoincrement=False, nullable=True
            ),
            sa.Column(
                'deleted', postgresql.TIMESTAMP(), autoincrement=False, nullable=True
            ),
            sa.PrimaryKeyConstraint('sessionId', name='sessionId_pkey'),
        )
    except Exception as ex:
        print(f"Failed to execute the migration script due to: {ex}")
        raise ex


def downgrade():
    """
    The script does the following migration:
        1) Deletes auth_session table
    """
    try:
        print("Dropping Auth Sessions Table...")
        op.drop_table('auth_session')
    except Exception as ex:
        print(f"Failed to execute the migration script due to: {ex}")
        raise ex
