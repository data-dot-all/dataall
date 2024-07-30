"""add_redshift_datasets

Revision ID: 852cdf6cf1e0
Revises: 7c5b30fee306
Create Date: 2024-07-25 08:25:34.122091

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.dialects import postgresql

from dataall.core.environment.db.environment_models import Environment
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService


# revision identifiers, used by Alembic.
revision = '852cdf6cf1e0'
down_revision = '7c5b30fee306'
branch_labels = None
depends_on = None

# Redshift permissions
LIST_ENVIRONMENT_REDSHIFT_CONNECTIONS = 'LIST_ENVIRONMENT_REDSHIFT_CONNECTIONS'
CREATE_REDSHIFT_CONNECTION = 'CREATE_REDSHIFT_CONNECTION'
IMPORT_REDSHIFT_DATASET = 'IMPORT_REDSHIFT_DATASET'

ENVIRONMENT_REDSHIFT_ALL = [LIST_ENVIRONMENT_REDSHIFT_CONNECTIONS, CREATE_REDSHIFT_CONNECTION, IMPORT_REDSHIFT_DATASET]


def upgrade():
    op.create_table(
        'redshift_connection',
        sa.Column('label', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('owner', sa.String(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=True),
        sa.Column('updated', sa.DateTime(), nullable=True),
        sa.Column('deleted', sa.DateTime(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('connectionUri', sa.String(), nullable=False),
        sa.Column('environmentUri', sa.String(), nullable=False),
        sa.Column('SamlGroupName', sa.String(), nullable=False),
        sa.Column('redshiftType', sa.String(), nullable=False),
        sa.Column('clusterId', sa.String(), nullable=True),
        sa.Column('nameSpaceId', sa.String(), nullable=True),
        sa.Column('workgroup', sa.String(), nullable=True),
        sa.Column('database', sa.String(), nullable=False),
        sa.Column('redshiftUser', sa.String(), nullable=True),
        sa.Column('secretArn', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ['environmentUri'],
            ['environment.environmentUri'],
        ),
        sa.PrimaryKeyConstraint('connectionUri'),
    )

    op.create_table(
        'redshift_dataset',
        sa.Column('datasetUri', sa.String(), nullable=False),
        sa.Column('connectionUri', sa.String(), nullable=False),
        sa.Column('schema', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ['connectionUri'],
            ['redshift_connection.connectionUri'],
        ),
        sa.ForeignKeyConstraint(
            ['datasetUri'],
            ['dataset.datasetUri'],
        ),
        sa.PrimaryKeyConstraint('datasetUri'),
    )

    op.create_table(
        'redshift_table',
        sa.Column('label', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('owner', sa.String(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=True),
        sa.Column('updated', sa.DateTime(), nullable=True),
        sa.Column('deleted', sa.DateTime(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('datasetUri', sa.String(), nullable=False),
        sa.Column('rsTableUri', sa.String(), nullable=False),
        sa.Column('topics', postgresql.ARRAY(sa.String()), nullable=True),
        sa.ForeignKeyConstraint(['datasetUri'], ['redshift_dataset.datasetUri'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('rsTableUri'),
    )
    try:
        op.execute("ALTER TYPE datasettypes ADD VALUE 'Redshift'")
    except Exception as e:
        if 'already exists' in str(e):
            pass
        else:
            raise e

    ## Backfilling Redshift permissions
    bind = op.get_bind()
    session = orm.Session(bind=bind)
    all_environments = session.query(Environment).all()
    for env in all_environments:
        ResourcePolicyService.attach_resource_policy(
            session=session,
            group=env.SamlGroupName,
            resource_uri=env.environmentUri,
            permissions=ENVIRONMENT_REDSHIFT_ALL,
            resource_type=Environment.__name__,
        )


def downgrade():
    op.drop_table('redshift_table')
    op.drop_table('redshift_dataset')
    op.drop_table('redshift_connection')
    # There is no postgres command to DELETE VALUE from an enum
    # In the official docs is recommended to leave it:
    # https://www.postgresql.org/message-id/21012.1459434338%40sss.pgh.pa.us

    # Deleting Redshift permissions
    bind = op.get_bind()
    session = orm.Session(bind=bind)
    all_environments = session.query(Environment).all()
    for env in all_environments:
        policies = ResourcePolicyService.find_resource_policies(
            session=session,
            group=env.SamlGroupName,
            resource_uri=env.environmentUri,
            resource_type=Environment.__name__,
            permissions=ENVIRONMENT_REDSHIFT_ALL,
        )
        for policy in policies:
            for permission in policy.permissions:
                session.delete(permission)
                session.commit()
