import json
import logging
import os
import sys
import typing

from botocore.exceptions import ClientError
from sqlalchemy import and_

from dataall.aws.handlers.sts import SessionHelper
from dataall.db import get_engine
from dataall.db import models
from dataall.modules.dataset_sharing.db.Enums import ShareObjectStatus
from dataall.modules.dataset_sharing.db.models import ShareObjectItem, ShareObject
from dataall.modules.datasets_base.db.models import DatasetStorageLocation, DatasetTable, Dataset

root = logging.getLogger()
root.setLevel(logging.INFO)
if not root.hasHandlers():
    root.addHandler(logging.StreamHandler(sys.stdout))
log = logging.getLogger(__name__)


class BucketPoliciesUpdater:
    def __init__(self, engine, event=None):
        self.engine = engine
        self.event = event
        self.reports = []

    def sync_imported_datasets_bucket_policies(self):
        with self.engine.scoped_session() as session:
            imported_datasets = (
                session.query(Dataset)
                .filter(
                    and_(
                        Dataset.imported == True,
                        Dataset.deleted.is_(None),
                    )
                )
                .all()
            )
            log.info(f'Found {len(imported_datasets)} imported datasets')

            for dataset in imported_datasets:
                account_prefixes = {}

                shared_tables = self.get_shared_tables(dataset)
                log.info(
                    f'Found {len(shared_tables)} shared tables with dataset {dataset.S3BucketName}'
                )

                shared_folders = self.get_shared_folders(dataset)
                log.info(
                    f'Found {len(shared_folders)} shared folders with dataset {dataset.S3BucketName}'
                )

                for table in shared_tables:
                    data_prefix = self.clear_table_location_from_delta_path(table)
                    prefix = data_prefix.rstrip('/') + '/*'
                    accountid = table.TargetAwsAccountId

                    prefix = f"arn:aws:s3:::{prefix.split('s3://')[1]}"
                    self.group_prefixes_by_accountid(
                        accountid, prefix, account_prefixes
                    )

                    bucket = (
                        f"arn:aws:s3:::{prefix.split('arn:aws:s3:::')[1].split('/')[0]}"
                    )
                    self.group_prefixes_by_accountid(
                        accountid, bucket, account_prefixes
                    )

                for folder in shared_folders:
                    prefix = f'arn:aws:s3:::{folder.S3Prefix}' + '/*'
                    accountid = folder.AwsAccountId
                    self.group_prefixes_by_accountid(
                        accountid, prefix, account_prefixes
                    )
                    bucket = (
                        f"arn:aws:s3:::{prefix.split('arn:aws:s3:::')[1].split('/')[0]}"
                    )
                    self.group_prefixes_by_accountid(
                        accountid, bucket, account_prefixes
                    )

                client = self.init_s3_client(dataset)

                policy = self.get_bucket_policy(client, dataset)

                BucketPoliciesUpdater.update_policy(account_prefixes, policy)

                report = self.put_bucket_policy(client, dataset, policy)

                self.reports.append(report)

            if any(r['status'] == 'FAILED' for r in self.reports):
                raise Exception(
                    'Failed to update one or more bucket policies'
                    f'Check the reports: {self.reports}'
                )
            return self.reports

    @staticmethod
    def clear_table_location_from_delta_path(table):
        data_prefix = (
            table.S3Prefix
            if '/packages.delta' not in table.S3Prefix
            else table.S3Prefix.replace('/packages.delta', '')
        )
        data_prefix = (
            data_prefix
            if '/_symlink_format_manifest' not in data_prefix
            else data_prefix.replace('/_symlink_format_manifest', '')
        )
        return data_prefix

    @staticmethod
    def update_policy(account_prefixes, policy):
        log.info('Updating Policy')
        statements = policy['Statement']
        for key, value in account_prefixes.items():
            added = False
            for s in statements:
                if key in s.get('Principal').get('AWS') and 'DA' in s.get('Sid'):
                    log.info(f'Principal already on the policy {key}')
                    added = True
                    for v in value:
                        if v not in s.get('Resource'):
                            existing_resources = (
                                list(s.get('Resource'))
                                if not isinstance(s.get('Resource'), list)
                                else s.get('Resource')
                            )
                            existing_resources.append(v)
                            s['Resource'] = existing_resources
                    break
            if not added:
                log.info(
                    f'Principal {key} with permissions {value} '
                    f'Not on the policy adding it'
                )
                statements.append(
                    {
                        'Sid': f'DA{key}',
                        'Effect': 'Allow',
                        'Action': ['s3:Get*', 's3:List*'],
                        'Resource': value
                        if isinstance(value, list) and len(value) > 1
                        else value,
                        'Principal': {'AWS': key},
                    }
                )
        policy.update({'Statement': statements})
        log.info(f'Final Policy --> {policy}')
        return policy

    @classmethod
    def group_prefixes_by_accountid(cls, accountid, prefix, account_prefixes):
        if account_prefixes.get(accountid):
            prefixes = account_prefixes[accountid]
            if prefix not in prefixes:
                prefixes.append(prefix)
            account_prefixes[accountid] = prefixes
        else:
            account_prefixes[accountid] = [prefix]
        return account_prefixes

    def get_shared_tables(self, dataset) -> typing.List[ShareObjectItem]:
        with self.engine.scoped_session() as session:
            tables = (
                session.query(
                    DatasetTable.GlueDatabaseName.label('GlueDatabaseName'),
                    DatasetTable.GlueTableName.label('GlueTableName'),
                    DatasetTable.S3Prefix.label('S3Prefix'),
                    DatasetTable.AWSAccountId.label('SourceAwsAccountId'),
                    DatasetTable.region.label('SourceRegion'),
                    models.Environment.AwsAccountId.label('TargetAwsAccountId'),
                    models.Environment.region.label('TargetRegion'),
                )
                .join(
                    ShareObjectItem,
                    and_(
                        ShareObjectItem.itemUri == DatasetTable.tableUri
                    ),
                )
                .join(
                    ShareObject,
                    ShareObject.shareUri == ShareObjectItem.shareUri,
                )
                .join(
                    models.Environment,
                    models.Environment.environmentUri
                    == ShareObject.environmentUri,
                )
                .filter(
                    and_(
                        DatasetTable.datasetUri == dataset.datasetUri,
                        DatasetTable.deleted.is_(None),
                        ShareObjectItem.status == ShareObjectStatus.Approved.value,
                    )
                )
            ).all()
        return tables

    def get_shared_folders(self, dataset) -> typing.List[DatasetStorageLocation]:
        with self.engine.scoped_session() as session:
            locations = (
                session.query(
                    DatasetStorageLocation.locationUri.label('locationUri'),
                    DatasetStorageLocation.S3BucketName.label('S3BucketName'),
                    DatasetStorageLocation.S3Prefix.label('S3Prefix'),
                    models.Environment.AwsAccountId.label('AwsAccountId'),
                    models.Environment.region.label('region'),
                )
                .join(
                    ShareObjectItem,
                    and_(
                        ShareObjectItem.itemUri
                        == DatasetStorageLocation.locationUri
                    ),
                )
                .join(
                    ShareObject,
                    ShareObject.shareUri == ShareObjectItem.shareUri,
                )
                .join(
                    models.Environment,
                    models.Environment.environmentUri
                    == ShareObject.environmentUri,
                )
                .filter(
                    and_(
                        DatasetStorageLocation.datasetUri == dataset.datasetUri,
                        DatasetStorageLocation.deleted.is_(None),
                        ShareObjectItem.status == ShareObjectStatus.Approved.value,
                    )
                )
            ).all()
        return locations

    @classmethod
    def init_s3_client(cls, dataset):
        session = SessionHelper.remote_session(accountid=dataset.AwsAccountId)
        client = session.client('s3')
        return client

    @classmethod
    def get_bucket_policy(cls, client, dataset):
        try:
            policy = client.get_bucket_policy(Bucket=dataset.S3BucketName)['Policy']
            log.info(f'Current bucket policy---->:{policy}')
            policy = json.loads(policy)
        except ClientError as err:
            if err.response['Error']['Code'] == 'NoSuchBucketPolicy':
                log.info(f"No policy attached to '{dataset.S3BucketName}'")

            elif err.response['Error']['Code'] == 'NoSuchBucket':
                log.error(f'Bucket deleted {dataset.S3BucketName}')

            elif err.response['Error']['Code'] == 'AccessDenied':
                log.error(
                    f'Access denied in {dataset.AwsAccountId} '
                    f'(s3:{err.operation_name}, '
                    f"resource='{dataset.S3BucketName}')"
                )
            else:
                log.exception(
                    f"Failed to get '{dataset.S3BucketName}' policy in {dataset.AwsAccountId}"
                )
            policy = {
                'Version': '2012-10-17',
                'Statement': [
                    {
                        'Sid': 'OwnerAccount',
                        'Effect': 'Allow',
                        'Action': ['s3:*'],
                        'Resource': [
                            f'arn:aws:s3:::{dataset.S3BucketName}',
                            f'arn:aws:s3:::{dataset.S3BucketName}/*',
                        ],
                        'Principal': {
                            'AWS': f'arn:aws:iam::{dataset.AwsAccountId}:root'
                        },
                    }
                ],
            }

        return policy

    @staticmethod
    def put_bucket_policy(s3_client, dataset, policy):
        update_policy_report = {
            'datasetUri': dataset.datasetUri,
            'bucketName': dataset.S3BucketName,
            'accountId': dataset.AwsAccountId,
        }
        try:
            policy_json = json.dumps(policy) if isinstance(policy, dict) else policy
            log.info(
                f"Putting new bucket policy on '{dataset.S3BucketName}' policy {policy_json}"
            )
            response = s3_client.put_bucket_policy(
                Bucket=dataset.S3BucketName, Policy=policy_json
            )
            log.info(f'Bucket Policy updated: {response}')
            update_policy_report.update({'status': 'SUCCEEDED'})
        except ClientError as e:
            log.error(
                f'Failed to update bucket policy '
                f"on '{dataset.S3BucketName}' policy {policy} "
                f'due to {e} '
            )
            update_policy_report.update({'status': 'FAILED'})

        return update_policy_report


if __name__ == '__main__':
    ENVNAME = os.environ.get('envname', 'local')
    ENGINE = get_engine(envname=ENVNAME)
    log.info('Updating bucket policies for shared datasets...')
    service = BucketPoliciesUpdater(engine=ENGINE)
    service.sync_imported_datasets_bucket_policies()
    log.info('Bucket policies for shared datasets update successfully...')
