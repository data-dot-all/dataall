import logging
import os
import sys
from operator import and_

from dataall.base.aws.sts import SessionHelper
from dataall.core.environment.db.environment_models import Environment, EnvironmentGroup
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.base.db import get_engine
from dataall.modules.datasets.aws.glue_dataset_client import DatasetCrawler
from dataall.modules.datasets.aws.lf_table_client import LakeFormationTableClient
from dataall.modules.datasets.services.dataset_table_service import DatasetTableService
from dataall.modules.datasets_base.db.dataset_repositories import DatasetRepository
from dataall.modules.datasets_base.db.dataset_models import DatasetTable, Dataset
from dataall.modules.datasets.indexers.table_indexer import DatasetTableIndexer
from dataall.modules.dataset_sharing.services.dataset_alarm_service import DatasetAlarmService

root = logging.getLogger()
root.setLevel(logging.INFO)
if not root.hasHandlers():
    root.addHandler(logging.StreamHandler(sys.stdout))
log = logging.getLogger(__name__)


def sync_tables(engine):
    with engine.scoped_session() as session:
        processed_tables = []
        all_datasets: [Dataset] = DatasetRepository.list_all_active_datasets(
            session
        )
        log.info(f'Found {len(all_datasets)} datasets for tables sync')
        dataset: Dataset
        for dataset in all_datasets:
            log.info(
                f'Synchronizing dataset {dataset.name}|{dataset.datasetUri} tables'
            )
            env: Environment = (
                session.query(Environment)
                .filter(
                    and_(
                        Environment.environmentUri == dataset.environmentUri,
                        Environment.deleted.is_(None),
                    )
                )
                .first()
            )
            env_group: EnvironmentGroup = (
                EnvironmentService.get_environment_group(
                    session, dataset.SamlAdminGroupName, env.environmentUri
                )
            )
            try:
                if not env or not is_assumable_pivot_role(env):
                    log.info(
                        f'Dataset {dataset.GlueDatabaseName} has an invalid environment'
                    )
                else:

                    tables = DatasetCrawler(dataset).list_glue_database_tables()

                    log.info(
                        f'Found {len(tables)} tables on Glue database {dataset.GlueDatabaseName}'
                    )

                    DatasetTableService.sync_existing_tables(
                        session, dataset.datasetUri, glue_tables=tables
                    )

                    tables = (
                        session.query(DatasetTable)
                        .filter(DatasetTable.datasetUri == dataset.datasetUri)
                        .all()
                    )

                    log.info('Updating tables permissions on Lake Formation...')

                    for table in tables:
                        LakeFormationTableClient(table).grant_principals_all_table_permissions(
                            principals=[
                                SessionHelper.get_delegation_role_arn(env.AwsAccountId),
                                env_group.environmentIAMRoleArn,
                            ],
                        )

                    processed_tables.extend(tables)

                    DatasetTableIndexer.upsert_all(session, dataset_uri=dataset.datasetUri)
            except Exception as e:
                log.error(
                    f'Failed to sync tables for dataset '
                    f'{dataset.AwsAccountId}/{dataset.GlueDatabaseName} '
                    f'due to: {e}'
                )
                DatasetAlarmService().trigger_dataset_sync_failure_alarm(dataset, str(e))
        return processed_tables


def is_assumable_pivot_role(env: Environment):
    aws_session = SessionHelper.remote_session(accountid=env.AwsAccountId)
    if not aws_session:
        log.error(
            f'Failed to assume dataall pivot role in environment {env.AwsAccountId}'
        )
        return False
    return True


if __name__ == '__main__':
    ENVNAME = os.environ.get('envname', 'local')
    ENGINE = get_engine(envname=ENVNAME)
    sync_tables(engine=ENGINE)
