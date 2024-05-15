"""rename_dataset_table_as_s3_dataset

Revision ID: d059eead99c2
Revises: 458572580709
Create Date: 2024-05-07 15:01:14.241572

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd059eead99c2'
down_revision = '458572580709'
branch_labels = None
depends_on = None


def upgrade():
    print('Renaming dataset as s3_dataset...')
    op.drop_constraint(constraint_name='fk_dataset_env_uri', table_name='dataset', type_='foreignkey')
    op.rename_table('dataset', 's3_dataset')
    op.execute('ALTER INDEX dataset_pkey RENAME TO s3_dataset_pkey')
    op.create_foreign_key(
        constraint_name='s3_dataset_environmentUri_fkey',
        source_table='s3_dataset',
        referent_table='environment',
        local_cols=['environmentUri'],
        remote_cols=['environmentUri'],
    )
    op.add_column(
        's3_dataset',
        sa.Column('datasetType', sa.String(), nullable=True),
    )
    op.execute('UPDATE s3_dataset SET "datasetType" = \'S3\'')
    op.alter_column('s3_dataset', 'datasetType', nullable=False)


def downgrade():
    print('Renaming s3_dataset as dataset...')
    op.drop_column('s3_dataset', 'datasetType')
    op.rename_table('s3_dataset', 'dataset')
    op.execute('ALTER INDEX s3_dataset_pkey RENAME TO dataset_pkey')
    op.create_foreign_key(
        constraint_name='fk_dataset_env_uri',
        source_table='dataset',
        referent_table='environment',
        local_cols=['environmentUri'],
        remote_cols=['environmentUri'],
    )
