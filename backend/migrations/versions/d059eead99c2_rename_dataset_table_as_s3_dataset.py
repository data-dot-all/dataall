"""rename_dataset_table_as_s3_dataset

Revision ID: d059eead99c2
Revises: 458572580709
Create Date: 2024-05-07 15:01:14.241572

"""

from alembic import op
import sqlalchemy as sa
from dataall.modules.datasets_base.services.datasets_enums import DatasetTypes

# revision identifiers, used by Alembic.
revision = 'd059eead99c2'
down_revision = 'b833ad41db68'
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
    op.execute("CREATE TYPE datasettypes AS ENUM('S3')")
    # To add values to types: op.execute("ALTER TYPE datasettypes ADD VALUE 'REDSHIFT'")
    op.add_column(
        's3_dataset',
        sa.Column(
            'datasetType',
            sa.Enum(DatasetTypes.S3.value, name='datasettypes'),
            nullable=False,
            server_default=DatasetTypes.S3.value,
        ),
    )


def downgrade():
    print('Renaming s3_dataset as dataset...')
    op.drop_constraint(constraint_name='s3_dataset_environmentUri_fkey', table_name='s3_dataset', type_='foreignkey')
    op.drop_column('s3_dataset', 'datasetType')
    op.execute('DROP TYPE datasettypes')
    op.rename_table('s3_dataset', 'dataset')
    op.execute('ALTER INDEX s3_dataset_pkey RENAME TO dataset_pkey')
    op.create_foreign_key(
        constraint_name='fk_dataset_env_uri',
        source_table='dataset',
        referent_table='environment',
        local_cols=['environmentUri'],
        remote_cols=['environmentUri'],
    )
