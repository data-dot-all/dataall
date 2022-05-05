import logging
import os
import sys
from operator import and_

from .. import db
from ..aws.handlers.glue import Glue
from ..aws.handlers.sts import SessionHelper
from ..db import get_engine
from ..db import models
from ..searchproxy import indexers
from ..searchproxy.connect import (
    connect,
)
from ..utils.alarm_service import AlarmService

root = logging.getLogger()
root.setLevel(logging.INFO)
if not root.hasHandlers():
    root.addHandler(logging.StreamHandler(sys.stdout))
log = logging.getLogger(__name__)


def sync_tables(engine, es=None):
    with engine.scoped_session() as session:
        processed_tables = []
        all_datasets: [models.Dataset] = db.api.Dataset.list_all_active_datasets(session)
        log.info(f"Found {len(all_datasets)} datasets for tables sync")
        dataset: models.Dataset
        for dataset in all_datasets:
            log.info(f"Synchronizing dataset {dataset.name}|{dataset.datasetUri} tables")
            env: models.Environment = (
                session.query(models.Environment)
                .filter(
                    and_(
                        models.Environment.environmentUri == dataset.environmentUri,
                        models.Environment.deleted.is_(None),
                    )
                )
                .first()
            )
            env_group: models.EnvironmentGroup = db.api.Environment.get_environment_group(
                session, dataset.SamlAdminGroupName, env.environmentUri
            )
            try:
                if not env or not is_assumable_pivot_role(env):
                    log.info(f"Dataset {dataset.GlueDatabaseName} has an invalid environment")
                else:

                    tables = Glue.list_glue_database_tables(
                        dataset.AwsAccountId, dataset.GlueDatabaseName, dataset.region
                    )

                    log.info(f"Found {len(tables)} tables on Glue database {dataset.GlueDatabaseName}")

                    db.api.DatasetTable.sync(session, dataset.datasetUri, glue_tables=tables)

                    tables = (
                        session.query(models.DatasetTable)
                        .filter(models.DatasetTable.datasetUri == dataset.datasetUri)
                        .all()
                    )

                    log.info("Updating tables permissions on Lake Formation...")

                    for table in tables:
                        Glue.grant_principals_all_table_permissions(
                            table,
                            principals=[
                                SessionHelper.get_delegation_role_arn(env.AwsAccountId),
                                env.EnvironmentDefaultIAMRoleArn,
                                env_group.environmentIAMRoleArn,
                            ],
                        )

                    processed_tables.extend(tables)

                    if es:
                        indexers.upsert_dataset_tables(session, es, dataset.datasetUri)
            except Exception as e:
                log.error(
                    f"Failed to sync tables for dataset "
                    f"{dataset.AwsAccountId}/{dataset.GlueDatabaseName} "
                    f"due to: {e}"
                )
                AlarmService().trigger_dataset_sync_failure_alarm(dataset, str(e))
        return processed_tables


def is_assumable_pivot_role(env: models.Environment):
    aws_session = SessionHelper.remote_session(accountid=env.AwsAccountId)
    if not aws_session:
        log.error(f"Failed to assume dataall pivot role in environment {env.AwsAccountId}")
        return False
    return True


if __name__ == "__main__":
    ENVNAME = os.environ.get("envname", "local")
    ENGINE = get_engine(envname=ENVNAME)
    ES = connect(envname=ENVNAME)
    sync_tables(engine=ENGINE, es=ES)
