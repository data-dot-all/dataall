import logging
from datetime import datetime

from dataall.core.environment.db.environment_models import Environment
from dataall.modules.shares_base.db.share_object_models import ShareObject
from dataall.modules.s3_datasets.db.dataset_models import DatasetTable, DatasetStorageLocation, DatasetBucket
from dataall.base.utils.alarm_service import AlarmService

log = logging.getLogger(__name__)


class S3ShareAlarmService(AlarmService):
    """Contains set of alarms for datasets"""

    def trigger_table_sharing_failure_alarm(
        self,
        table: DatasetTable,
        share: ShareObject,
        target_environment: Environment,
    ):
        log.info('Triggering share failure alarm...')
        subject = f'Data.all Share Failure for Table {table.GlueTableName}'[:100]
        message = f"""
    You are receiving this email because your Data.all {self.envname} environment in the {self.region} region has entered the ALARM state, because it failed to share the table {table.GlueTableName} with Lake Formation.

    Alarm Details:
        - State Change:               	OK -> ALARM
        - Reason for State Change:      Lake Formation sharing failure
        - Timestamp:                              {datetime.now()}

        Share Source
        - Dataset URI:                   {share.datasetUri}
        - AWS Account:                {table.AWSAccountId}
        - Region:                            {table.region}
        - Glue Database:              {table.GlueDatabaseName}
        - Glue Table:                     {table.GlueTableName}

        Share Target
        - AWS Account:                {target_environment.AwsAccountId}
        - Region:                            {target_environment.region}
        - Glue Database:              {table.GlueDatabaseName}shared
    """
        return self.publish_message_to_alarms_topic(subject, message)

    def trigger_revoke_table_sharing_failure_alarm(
        self,
        table: DatasetTable,
        share: ShareObject,
        target_environment: Environment,
    ):
        log.info('Triggering share failure alarm...')
        subject = f'Data.all Revoke LF Permissions Failure for Table {table.GlueTableName}'[:100]
        message = f"""
    You are receiving this email because your Data.all {self.envname} environment in the {self.region} region has entered the ALARM state, because it failed to revoke Lake Formation permissions for table {table.GlueTableName} with Lake Formation.

    Alarm Details:
        - State Change:               	OK -> ALARM
        - Reason for State Change:      Lake Formation sharing failure
        - Timestamp:                              {datetime.now()}

        Share Source
        - Dataset URI:                   {share.datasetUri}
        - AWS Account:                {table.AWSAccountId}
        - Region:                            {table.region}
        - Glue Database:              {table.GlueDatabaseName}
        - Glue Table:                     {table.GlueTableName}

        Share Target
        - AWS Account:                {target_environment.AwsAccountId}
        - Region:                            {target_environment.region}
        - Glue Database:              {table.GlueDatabaseName}shared
    """
        return self.publish_message_to_alarms_topic(subject, message)

    def trigger_folder_sharing_failure_alarm(
        self,
        folder: DatasetStorageLocation,
        share: ShareObject,
        target_environment: Environment,
    ):
        log.info('Triggering share failure alarm...')
        subject = f'Data.all Folder Share Failure for {folder.S3Prefix}'[:100]
        message = f"""
You are receiving this email because your Data.all {self.envname} environment in the {self.region} region has entered the ALARM state, because it failed to share the folder {folder.S3Prefix} with S3 Access Point.
Alarm Details:
    - State Change:               	OK -> ALARM
    - Reason for State Change:      S3 Folder sharing failure
    - Timestamp:                              {datetime.now()}
    Share Source
    - Dataset URI:                   {share.datasetUri}
    - AWS Account:                   {folder.AWSAccountId}
    - Region:                            {folder.region}
    - S3 Bucket:                     {folder.S3BucketName}
    - S3 Folder:                     {folder.S3Prefix}
    Share Target
    - AWS Account:                {target_environment.AwsAccountId}
    - Region:                            {target_environment.region}
"""
        return self.publish_message_to_alarms_topic(subject, message)

    def trigger_revoke_folder_sharing_failure_alarm(
        self,
        folder: DatasetStorageLocation,
        share: ShareObject,
        target_environment: Environment,
    ):
        log.info('Triggering share failure alarm...')
        subject = f'Data.all Folder Share Revoke Failure for {folder.S3Prefix}'[:100]
        message = f"""
You are receiving this email because your Data.all {self.envname} environment in the {self.region} region has entered the ALARM state, because it failed to share the folder {folder.S3Prefix} with S3 Access Point.
Alarm Details:
    - State Change:               	OK -> ALARM
    - Reason for State Change:      S3 Folder sharing Revoke failure
    - Timestamp:                              {datetime.now()}
    Share Source
    - Dataset URI:                   {share.datasetUri}
    - AWS Account:                   {folder.AWSAccountId}
    - Region:                            {folder.region}
    - S3 Bucket:                     {folder.S3BucketName}
    - S3 Folder:                     {folder.S3Prefix}
    Share Target
    - AWS Account:                {target_environment.AwsAccountId}
    - Region:                            {target_environment.region}
"""
        return self.publish_message_to_alarms_topic(subject, message)

    def trigger_s3_bucket_sharing_failure_alarm(
        self,
        bucket: DatasetBucket,
        share: ShareObject,
        target_environment: Environment,
    ):
        alarm_type = 'Share'
        return self.handle_bucket_sharing_failure(bucket, share, target_environment, alarm_type)

    def trigger_revoke_s3_bucket_sharing_failure_alarm(
        self,
        bucket: DatasetBucket,
        share: ShareObject,
        target_environment: Environment,
    ):
        alarm_type = 'Sharing Revoke'
        return self.handle_bucket_sharing_failure(bucket, share, target_environment, alarm_type)

    def handle_bucket_sharing_failure(
        self, bucket: DatasetBucket, share: ShareObject, target_environment: Environment, alarm_type: str
    ):
        log.info(f'Triggering {alarm_type} failure alarm...')
        subject = f'Data.all S3 Bucket Failure for {bucket.S3BucketName} {alarm_type}'[:100]
        message = f"""
You are receiving this email because your Data.all {self.envname} environment in the {self.region} region has entered the ALARM state, because it failed to {alarm_type} the S3 Bucket {bucket.S3BucketName}.
Alarm Details:
    - State Change:               	OK -> ALARM
    - Reason for State Change:      S3 Bucket {alarm_type} failure
    - Timestamp:                              {datetime.now()}
    Share Source
    - Dataset URI:                   {share.datasetUri}
    - AWS Account:                   {bucket.AwsAccountId}
    - Region:                            {bucket.region}
    - S3 Bucket:                     {bucket.S3BucketName}
    Share Target
    - AWS Account:                {target_environment.AwsAccountId}
    - Region:                            {target_environment.region}
"""
        return self.publish_message_to_alarms_topic(subject, message)
