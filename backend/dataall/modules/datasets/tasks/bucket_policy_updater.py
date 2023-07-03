import json
import logging
import os
import sys

from sqlalchemy import and_

from dataall.db import get_engine
from dataall.modules.dataset_sharing.db.share_object_repository import ShareObjectRepository
from dataall.modules.datasets.aws.s3_dataset_client import S3BucketPolicyClient
from dataall.modules.datasets_base.db.models import Dataset

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

                shared_tables = ShareObjectRepository.get_shared_tables(session, dataset)
                log.info(
                    f'Found {len(shared_tables)} shared tables with dataset {dataset.S3BucketName}'
                )

                shared_folders = ShareObjectRepository.get_shared_folders(session, dataset)
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

                client = S3BucketPolicyClient(dataset)

                policy = client.get_bucket_policy()

                BucketPoliciesUpdater.update_policy(account_prefixes, policy)

                report = client.put_bucket_policy(policy)

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


if __name__ == '__main__':
    ENVNAME = os.environ.get('envname', 'local')
    ENGINE = get_engine(envname=ENVNAME)
    log.info('Updating bucket policies for shared datasets...')
    service = BucketPoliciesUpdater(engine=ENGINE)
    service.sync_imported_datasets_bucket_policies()
    log.info('Bucket policies for shared datasets update successfully...')
