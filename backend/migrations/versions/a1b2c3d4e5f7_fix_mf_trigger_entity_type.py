"""fix_mf_trigger_entity_type
Revision ID: a1b2c3d4e5f7
Revises: ba2da94739ab
Create Date: 2025-10-03 12:00:00.000000
"""

from alembic import op
import os

# revision identifiers used by Alembic.
revision = 'a1b2c3d4e5f7'
down_revision = 'ba2da94739ab'
branch_labels = None
depends_on = None

ENVNAME = os.getenv('envname', 'local')


def upgrade():
    # Fix the entity type in the dataset delete trigger function
    # Original had 'Dataset' (generic), should be 'S3-Dataset' (specific to S3 datasets)
    SQL_DATASET_TRIGGER_DEF = """
        CREATE OR REPLACE FUNCTION dataset_delete_trigger_function()
        RETURNS TRIGGER AS $$
        BEGIN
            DELETE FROM {SCHEMA_NAME}.attached_metadata_form
            WHERE "entityUri" = OLD."datasetUri"
              AND "entityType" = 'S3-Dataset';
            RETURN OLD;
        END;
        $$ LANGUAGE plpgsql;
    """.format(SCHEMA_NAME=ENVNAME)

    op.execute(SQL_DATASET_TRIGGER_DEF)  # nosemgrep


def downgrade():
    # Revert back to the original version
    SQL_DATASET_TRIGGER_DEF = """
        CREATE OR REPLACE FUNCTION dataset_delete_trigger_function()
        RETURNS TRIGGER AS $$
        BEGIN
            DELETE FROM {SCHEMA_NAME}.attached_metadata_form
            WHERE "entityUri" = OLD."datasetUri"
              AND "entityType" = 'Dataset';
            RETURN OLD;
        END;
        $$ LANGUAGE plpgsql;
    """.format(SCHEMA_NAME=ENVNAME)

    op.execute(SQL_DATASET_TRIGGER_DEF)  # nosemgrep
