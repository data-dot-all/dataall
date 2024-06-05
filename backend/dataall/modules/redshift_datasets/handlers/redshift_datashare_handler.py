import logging

from dataall.core.tasks.service_handlers import Worker
from dataall.core.tasks.db.task_models import Task
from dataall.modules.redshift_datasets.db.redshift_dataset_repositories import RedshiftDatasetRepository
from dataall.modules.redshift_datasets.db.redshift_connection_repositories import RedshiftConnectionRepository
from dataall.modules.redshift_datasets.db.redshift_models import RedshiftDataset, RedshiftConnection
from dataall.modules.redshift_datasets.aws.redshift_data import RedshiftData
from dataall.modules.redshift_datasets.aws.redshift import Redshift
from dataall.modules.redshift_datasets.aws.lakeformation import LakeFormation

log = logging.getLogger(__name__)


class RedshiftDataShareHandler:
    @staticmethod
    @Worker.handler(path='redshift.datashare.import')
    def create_redshift_datashare_to_catalog(engine, task: Task):
        with engine.scoped_session() as session:
            dataset: RedshiftDataset = RedshiftDatasetRepository.get_redshift_dataset_by_uri(session, task.targetUri)
            datashare_name = dataset.datashareArn.split('/')[-1]
            connection: RedshiftConnection = RedshiftConnectionRepository.find_redshift_connection(
                session, dataset.connectionUri
            )

            redshift_data_client = RedshiftData(
                account_id=dataset.AwsAccountId, region=dataset.region, connection=connection, dataset=dataset
            )
            redshift_data_client.create_datashare(datashare=datashare_name)
            redshift_data_client.grant_usage_to_datashare_via_catalog(
                datashare=datashare_name, account=dataset.AwsAccountId
            )

            redshift_client = Redshift(account_id=dataset.AwsAccountId, region=dataset.region)
            redshift_client.authorize_catalog_datashare(
                datashare_arn=dataset.datashareArn, account=dataset.AwsAccountId
            )

            lakeformation_client = LakeFormation(account_id=dataset.AwsAccountId, region=dataset.region)
            lakeformation_client.register_resource_datashare(datashare_arn=dataset.datashareArn)
            return dataset
