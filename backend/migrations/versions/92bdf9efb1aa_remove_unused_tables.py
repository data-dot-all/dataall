"""remove_unused_tables

Revision ID: 92bdf9efb1aa
Revises: 5fc49baecea4
Create Date: 2023-05-22 10:00:07.432462

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import orm


# revision identifiers, used by Alembic.
revision = '92bdf9efb1aa'
down_revision = '5fc49baecea4'
branch_labels = None
depends_on = None


def upgrade():
    try:
        bind = op.get_bind()
        session = orm.Session(bind=bind)
        print('Dropping worksheet_share table...')
        op.drop_table('worksheet_share')
        session.commit()
    except Exception as e:
        print(f'Failed to execute the migration script due to: {e}')


def downgrade():
    try:
        bind = op.get_bind()
        session = orm.Session(bind=bind)
        print('Creating worksheet_share table...')
        op.create_table(
            'worksheet_share',
            sa.Column('worksheetShareUri', sa.String(), nullable=False),
            sa.Column('worksheetUri', sa.String(), nullable=False),
            sa.Column('principalId', sa.String(), nullable=False),
            sa.Column('principalType', sa.String(), nullable=False),
            sa.Column('canEdit', sa.Boolean(), nullable=True),
            sa.Column('owner', sa.String(), nullable=False),
            sa.Column('created', sa.DateTime(), nullable=True),
            sa.Column('updated', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('worksheetShareUri'),
        )
        session.commit()
    except Exception as e:
        print(f'Failed to execute the migration script due to: {e}')
