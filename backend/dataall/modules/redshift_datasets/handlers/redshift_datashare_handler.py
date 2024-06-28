import logging

from dataall.core.tasks.service_handlers import Worker
from dataall.core.tasks.db.task_models import Task
from dataall.modules.redshift_datasets.db.redshift_dataset_repositories import RedshiftDatasetRepository
from dataall.modules.redshift_datasets.db.redshift_connection_repositories import RedshiftConnectionRepository
from dataall.modules.redshift_datasets.db.redshift_models import RedshiftDataset, RedshiftConnection, RedshiftTable
from dataall.modules.redshift_datasets.aws.redshift_data import RedshiftData
from dataall.modules.redshift_datasets.aws.redshift import Redshift
from dataall.modules.redshift_datasets.aws.lakeformation import LakeFormation
from dataall.modules.redshift_datasets.aws.glue import Glue

log = logging.getLogger(__name__)


class RedshiftDataShareHandler:
    @staticmethod
    @Worker.handler(path='redshift.datashare.import')
    def create_redshift_datashare_to_catalog(engine, task: Task):
        with engine.scoped_session() as session:
            dataset: RedshiftDataset = RedshiftDatasetRepository.get_redshift_dataset_by_uri(session, task.targetUri)
            tables: [RedshiftTable] = RedshiftDatasetRepository.list_redshift_dataset_tables(session, dataset.datasetUri)
            datashare_name = dataset.datashareArn.split('/')[-1]
            connection: RedshiftConnection = RedshiftConnectionRepository.find_redshift_connection(
                session, dataset.connectionUri
            )

            redshift_data_client = RedshiftData(
                account_id=dataset.AwsAccountId, region=dataset.region, connection=connection
            )
            redshift_data_client.create_datashare(datashare=datashare_name, schema=dataset.schema)
            for table in tables:
                redshift_data_client.add_table_to_datashare(
                    datashare=datashare_name, schema=dataset.schema, table_name=table.name)
            redshift_data_client.grant_usage_to_datashare_via_catalog(
                datashare=datashare_name, account=dataset.AwsAccountId
            )

            redshift_client = Redshift(account_id=dataset.AwsAccountId, region=dataset.region)
            redshift_client.authorize_datashare_to_catalog(
                datashare_arn=dataset.datashareArn, account=dataset.AwsAccountId
            )
            redshift_client.associate_data_share_catalog(
                datashare_arn=dataset.datashareArn, account=dataset.AwsAccountId, region=dataset.region
            )

            lakeformation_client = LakeFormation(account_id=dataset.AwsAccountId, region=dataset.region)
            lakeformation_client.register_resource_datashare(datashare_arn=dataset.datashareArn)

            glue_client = Glue(account_id=dataset.AwsAccountId, region=dataset.region)
            glue_client.create_database_from_redshift_datashare(
                name=dataset.label, datashare_arn=dataset.datashareArn, account=dataset.AwsAccountId
            )
