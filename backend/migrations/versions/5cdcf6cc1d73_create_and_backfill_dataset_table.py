"""create_and_backfill_dataset_table

Revision ID: 5cdcf6cc1d73
Revises: d059eead99c2
Create Date: 2024-05-07 15:24:09.833007

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '5cdcf6cc1d73'
down_revision = 'd059eead99c2'
branch_labels = None
depends_on = None


def upgrade():
    print('Creating dataset table...')
    new_dataset_table = op.create_table(
        'dataset',
        sa.Column('label', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('owner', sa.String(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=True),
        sa.Column('updated', sa.DateTime(), nullable=True),
        sa.Column('deleted', sa.DateTime(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('environmentUri', sa.String(), nullable=False),
        sa.Column('organizationUri', sa.String(), nullable=False),
        sa.Column('datasetUri', sa.String(), nullable=False),
        sa.Column('region', sa.String(), nullable=True),
        sa.Column('AwsAccountId', sa.String(), nullable=False),
        sa.Column('language', sa.String(), nullable=False),
        sa.Column('topics', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('confidentiality', sa.String(), nullable=False),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('businessOwnerEmail', sa.String(), nullable=True),
        sa.Column('businessOwnerDelegationEmails', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('stewards', sa.String(), nullable=True),
        sa.Column('SamlAdminGroupName', sa.String(), nullable=True),
        sa.Column('autoApprovalEnabled', sa.Boolean(), nullable=True),
        sa.Column('datasetType', sa.String(), nullable=False),
        sa.Column('imported', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(
            ['environmentUri'],
            ['environment.environmentUri'],
        ),
        sa.PrimaryKeyConstraint('datasetUri'),
    )
    op.create_foreign_key('dataset_datasetUri_fkey', 's3_dataset', 'dataset', ['datasetUri'], ['datasetUri'])

    # Update foreign keys of dataset_bucket -> to s3_dataset and dataset_lock -> to dataset tables
    op.drop_constraint('dataset_lock_datasetUri_fkey', 'dataset_lock', type_='foreignkey')
    op.create_foreign_key('dataset_lock_datasetUri_fkey', 'dataset_lock', 'dataset', ['datasetUri'], ['datasetUri'])

    op.drop_constraint('dataset_bucket_datasetUri_fkey', 'dataset_bucket', type_='foreignkey')
    op.create_foreign_key(
        's3_dataset_bucket_datasetUri_fkey',
        'dataset_bucket',
        's3_dataset',
        ['datasetUri'],
        ['datasetUri'],
        ondelete='CASCADE',
    )

    print('Backfill dataset with s3_dataset data...')
    # Read s3_datasets table rows
    conn = op.get_bind()
    res = conn.execute(
        'select label, name, owner, created, updated, deleted, description, "environmentUri", "organizationUri", "datasetUri", region, "AwsAccountId",  "language", topics, confidentiality, tags, "businessOwnerEmail", "businessOwnerDelegationEmails", stewards, "SamlAdminGroupName", "autoApprovalEnabled", "datasetType", imported  from s3_dataset'
    )
    results = res.fetchall()
    s3_datasets_info = [
        {
            'label': r[0],
            'name': r[1],
            'owner': r[2],
            'created': r[3],
            'updated': r[4],
            'deleted': r[5],
            'description': r[6],
            'environmentUri': r[7],
            'organizationUri': r[8],
            'datasetUri': r[9],
            'region': r[10],
            'AwsAccountId': r[11],
            'language': r[12],
            'topics': r[13],
            'confidentiality': r[14],
            'tags': r[15],
            'businessOwnerEmail': r[16],
            'businessOwnerDelegationEmails': r[17],
            'stewards': r[18],
            'SamlAdminGroupName': r[19],
            'autoApprovalEnabled': r[20],
            'datasetType': r[21],
            'imported': r[22],
        }
        for r in results
    ]

    # Insert s3_datasets_info into new datasets table.
    op.bulk_insert(new_dataset_table, s3_datasets_info)

    # ### end Alembic commands ###


def downgrade():
    op.drop_table('dataset')

    # Update foreign keys of dataset_bucket -> to s3_dataset and dataset_lock -> to dataset tables
    op.drop_constraint('dataset_lock_datasetUri_fkey', 'dataset_lock', type_='foreignkey')
    op.create_foreign_key('dataset_lock_datasetUri_fkey', 'dataset_lock', 's3_dataset', ['datasetUri'], ['datasetUri'])

    op.drop_constraint('s3_dataset_bucket_datasetUri_fkey', 'dataset_bucket', type_='foreignkey')
    op.create_foreign_key(
        'dataset_bucket_datasetUri_fkey',
        'dataset_bucket',
        's3_dataset',
        ['datasetUri'],
        ['datasetUri'],
        ondelete='CASCADE',
    )
    # ### end Alembic commands ###
