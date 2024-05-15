"""
The handler of this module will be called once upon every deployment
"""

import logging
import os
import datetime
import boto3
import time
from alembic import command
from alembic.script import ScriptDirectory
from alembic.migration import MigrationContext
from alembic.config import Config
from dataall.base.db.connection import ENVNAME, get_engine

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))


def handler(event, context) -> None:
    """
    This function will be called once upon every deployment.
    It checks if there are any alembic migration scripts to execute.
    If there are, it will create a snapshot of the database.
    It executes the alembic migration scripts.
    """
    alembic_cfg = Config('alembic.ini')
    alembic_cfg.set_main_option('script_location', './migrations')

    # Get head version
    script = ScriptDirectory.from_config(alembic_cfg)
    head_rev = script.get_current_head()

    # Get current version from database
    engine = get_engine(ENVNAME)
    with engine.engine.connect() as connection:
        context = MigrationContext.configure(connection)
        current_rev = context.get_current_revision()

    if head_rev != current_rev:
        snapshot_id = f'{os.environ.get("resource_prefix", "dataall")}-migration-{head_rev}-{datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}'
        cluster_id = engine.dbconfig.host.split('.')[0]
        logger.info(
            f'Creating RDS snapshot for cluster {cluster_id}, head revision {head_rev} is ahead of {current_rev}...'
        )
        try:
            rds_client = boto3.client('rds', region_name=os.getenv('AWS_REGION'))
            # Edge case in which the cluster is performing backup and/or maintenance operations.
            # If it times out the CICD pipeline fails and needs to be retried.
            while (
                cluster_status := rds_client.describe_db_clusters(DBClusterIdentifier=cluster_id)['DBClusters'][0][
                    'Status'
                ]
            ) != 'available':
                logger.info(f'Waiting while the cluster is available, {cluster_status=}')
                time.sleep(30)

            rds_client.create_db_cluster_snapshot(
                DBClusterSnapshotIdentifier=snapshot_id,
                DBClusterIdentifier=cluster_id,
                Tags=[
                    {'Key': 'Application', 'Value': 'dataall'},
                ],
            )
        except Exception as e:
            logger.exception(f'Failed to create RDS snapshot: {e}')
            raise Exception(f'Failed to create RDS snapshot: {e}')
