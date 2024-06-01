import logging
from datetime import datetime


from dataall.modules.s3_datasets.db.dataset_models import S3Dataset
from dataall.base.utils.alarm_service import AlarmService

log = logging.getLogger(__name__)


class DatasetAlarmService(AlarmService):
    """Contains set of alarms for datasets"""

    def trigger_dataset_sync_failure_alarm(self, dataset: S3Dataset, error: str):
        log.info(f'Triggering dataset {dataset.name} tables sync failure alarm...')
        subject = f'Data.all Dataset Tables Sync Failure for {dataset.name}'[:100]
        message = f"""
You are receiving this email because your Data.all {self.envname} environment in the {self.region} region has entered the ALARM state, because it failed to synchronize Dataset {dataset.name} tables from AWS Glue to the Search Catalog.

Alarm Details:
    - State Change:               	OK -> ALARM
    - Reason for State Change:      {error}
    - Timestamp:                              {datetime.now()}
    Dataset
     - Dataset URI:                   {dataset.datasetUri}
     - AWS Account:                {dataset.AwsAccountId}
     - Region:                            {dataset.region}
     - Glue Database:              {dataset.GlueDatabaseName}
    """
        return self.publish_message_to_alarms_topic(subject, message)
