# This  module is a wrapper for the cdk cli
# Python native subprocess package is used to spawn cdk [deploy|destroy] commands with appropriate parameters.
# Additionally, it uses the cdk plugin cdk-assume-role-credential-plugin to run cdk commands on target accounts
# see : https://github.com/aws-samples/cdk-assume-role-credential-plugin

import logging
import os
from datetime import datetime

from botocore.exceptions import ClientError

from ..aws.handlers.sts import SessionHelper
from ..db import models

logger = logging.getLogger(__name__)


class AlarmService:
    def __init__(self):
        self.envname = os.getenv('envname', 'local')
        self.region = os.environ.get('AWS_REGION', 'eu-west-1')

    def trigger_stack_deployment_failure_alarm(self, stack: models.Stack):
        logger.info('Triggering deployment failure alarm...')
        subject = f'ALARM: DATAALL Stack {stack.name} Deployment Failure Notification'
        message = f"""
You are receiving this email because your DATAALL {self.envname} environment in the {self.region} region has entered the ALARM state, because it failed to deploy one of its resource CloudFormation stacks {stack.name}

View the ECS task logs in the AWS Management Console:
https://{self.region}.console.aws.amazon.com/cloudwatch/deeplink.js?region=eu-west-1#logsV2:log-groups/log-group/$252Fdataall$252F{self.envname}$252Fecs$252Fcdkproxy/log-events/task$252Fcontainer$252F{stack.EcsTaskArn.split('/')[-1]}

Alarm Details:
- Stack Name:                           {stack.name}
- AWS Account:                        {stack.accountid}
- Region:                                    {stack.region}
- State Change:                        OK -> ALARM
- Reason for State Change:    Stack Deployment Failure
- Timestamp:                            {datetime.now()}
- CW Log Group:                      {f"/dataall/{self.envname}/cdkproxy/{stack.EcsTaskArn.split('/')[-1]}"}
"""
        return self.publish_message_to_alarms_topic(subject, message)

    def trigger_table_sharing_failure_alarm(
        self,
        table: models.DatasetTable,
        share: models.ShareObject,
        target_environment: models.Environment,
    ):
        logger.info('Triggering share failure alarm...')
        subject = (
            f'ALARM: DATAALL Table {table.GlueTableName} Sharing Failure Notification'
        )
        message = f"""
You are receiving this email because your DATAALL {self.envname} environment in the {self.region} region has entered the ALARM state, because it failed to share the table {table.GlueTableName} with Lake Formation.

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
        folder: models.DatasetStorageLocation,
        share: models.ShareObject,
        target_environment: models.Environment,
    ):
        logger.info('Triggering share failure alarm...')
        subject = (
            f'ALARM: DATAALL Folder {folder.S3Prefix} Sharing Failure Notification'
        )
        message = f"""
You are receiving this email because your DATAALL {self.envname} environment in the {self.region} region has entered the ALARM state, because it failed to share the folder {folder.S3Prefix} with S3 Access Point.

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

    def trigger_revoke_sharing_failure_alarm(
        self,
        table: models.DatasetTable,
        share: models.ShareObject,
        target_environment: models.Environment,
    ):
        logger.info('Triggering share failure alarm...')
        subject = f'ALARM: DATAALL Table {table.GlueTableName} Revoking LF permissions Failure Notification'
        message = f"""
You are receiving this email because your DATAALL {self.envname} environment in the {self.region} region has entered the ALARM state, because it failed to revoke Lake Formation permissions for table {table.GlueTableName} with Lake Formation.

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

    def trigger_catalog_indexing_failure_alarm(self, error: str):
        logger.info('Triggering catalog indexing failure alarm...')
        subject = 'ALARM: DATAALL Catalog Indexing Failure Notification'
        message = f"""
You are receiving this email because your DATAALL {self.envname} environment in the {self.region} region has entered the ALARM state, because it failed to index new items into OpenSearch.

Alarm Details:
    - State Change:               	OK -> ALARM
    - Reason for State Change:      {error}
    - Timestamp:                              {datetime.now()}
"""
        return self.publish_message_to_alarms_topic(subject, message)

    def trigger_dataset_sync_failure_alarm(self, dataset: models.Dataset, error: str):
        logger.info(f'Triggering dataset {dataset.name} tables sync failure alarm...')
        subject = (
            f'ALARM: DATAALL Dataset {dataset.name} Tables Sync Failure Notification'
        )
        message = f"""
You are receiving this email because your DATAALL {self.envname} environment in the {self.region} region has entered the ALARM state, because it failed to synchronize Dataset {dataset.name} tables from AWS Glue to the Search Catalog.

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

    def publish_message_to_alarms_topic(self, subject, message):
        if self.envname in ['local', 'pytest', 'dkrcompose']:
            logger.debug('Running in local mode...SNS topic not available')
        else:
            region = os.getenv('AWS_REGION', 'eu-west-1')
            session = SessionHelper.get_session()
            ssm = session.client('ssm', region_name=region)
            sns = session.client('sns', region_name=region)
            alarms_topic_arn = ssm.get_parameter(
                Name=f'/dataall/{self.envname}/sns/alarmsTopic'
            )['Parameter']['Value']
            try:
                logger.info('Sending deployment failure notification')
                response = sns.publish(
                    TopicArn=alarms_topic_arn,
                    Subject=subject,
                    Message=message,
                )
                return response
            except ClientError as e:
                logger.error(f'Failed to deliver message due to: {e} ')
                raise e
