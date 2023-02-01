import logging
import uuid

from ..common.lf_share_revoke import LFShareRevoke
from ....aws.handlers.lakeformation import LakeFormation
from ....aws.handlers.ram import Ram
from ....aws.handlers.sts import SessionHelper
from ....db import api, models
from ....aws.handlers.glue import Glue

log = logging.getLogger(__name__)


class LFTagShareRevoke:
    def __init__(
        self,
        session,
        source_env_list: list,
        tagged_datasets: [models.Dataset],
        tagged_tables: [models.DatasetTable],
        tagged_columns: [models.DatasetTableColumn],
        lftag_share: models.LFTagShareObject,
        target_environment:  models.Environment
    ):
        self.session = session
        self.source_env_list = source_env_list
        self.tagged_datasets = tagged_datasets
        self.tagged_tables = tagged_tables
        self.tagged_columns = tagged_columns
        self.target_environment = target_environment
        self.lftag_share = lftag_share

    def revoke_share(self) -> bool:
 
        principalIAMRoleARN = f"arn:aws:iam::{self.target_environment.AwsAccountId}:role/{self.lftag_share.principalIAMRoleName}"
        
        for db in self.tagged_datasets:
            if db.AwsAccountId != self.target_environment.AwsAccountId:
                shared_db_name = (db.GlueDatabaseName + '_shared_' + self.lftag_share.lftagShareUri)[:254]

                # Delete a resource link to the shared DB
                Glue.delete_database(
                    accountid=self.target_environment.AwsAccountId,
                    region=self.target_environment.region,
                    database=shared_db_name,
                    role_arn=principalIAMRoleARN
                )
                log.info("RESOURCE LINK DB DELETED")
        
        for table in self.tagged_tables:
            if table.AWSAccountId != self.target_environment.AwsAccountId:
                shared_db_name = (table.GlueDatabaseName + '_shared_' + self.lftag_share.lftagShareUri)[:254]
                # Delete a resource link to the shared Table
                Glue.batch_delete_tables(
                    accountid=self.target_environment.AwsAccountId,
                    region=self.target_environment.region,
                    database=shared_db_name,
                    tables=[table.GlueTableName],
                    role_arn=principalIAMRoleARN
                )
                log.info("RESOURCE LINK TABLE-COLS DELETED")
                
                hasTables = Glue.has_tables(
                    accountid=self.target_environment.AwsAccountId,
                    region=self.target_environment.region,
                    database=shared_db_name,
                    role_arn=principalIAMRoleARN
                )

                if not hasTables:
                    Glue.delete_database(
                        accountid=self.target_environment.AwsAccountId,
                        region=self.target_environment.region,
                        database=shared_db_name,
                        role_arn=principalIAMRoleARN
                    )
        
        for col in self.tagged_columns:
            if col.AWSAccountId != self.target_environment.AwsAccountId:
                shared_db_name = (col.GlueDatabaseName + '_shared_' + self.lftag_share.lftagShareUri)[:254]
                # Delete a resource link to the shared Table
                Glue.batch_delete_tables(
                    accountid=self.target_environment.AwsAccountId,
                    region=self.target_environment.region,
                    database=shared_db_name,
                    tables=[col.GlueTableName],
                    role_arn=principalIAMRoleARN
                )
                log.info("RESOURCE LINK TABLE-COLS DELETED")
                
                hasTables = Glue.has_tables(
                    accountid=self.target_environment.AwsAccountId,
                    region=self.target_environment.region,
                    database=shared_db_name,
                    role_arn=principalIAMRoleARN
                )
                if not hasTables:
                    Glue.delete_database(
                        accountid=self.target_environment.AwsAccountId,
                        region=self.target_environment.region,
                        database=shared_db_name,
                        role_arn=principalIAMRoleARN
                    )

        
        # Delete External LF Tag Expressions Data Permissions 
        for source_env in self.source_env_list:
            log.info(
                f'Revoking Access for External Principal: {principalIAMRoleARN}'
            )
            aws_session = SessionHelper.remote_session(accountid=source_env['account'])
            client = aws_session.client('lakeformation', region_name=source_env['region'])
            revoke_entries = [
                {
                    'Id': str(uuid.uuid4()),
                    'Principal': {
                        'DataLakePrincipalIdentifier': principalIAMRoleARN
                    },
                    'Resource': {
                        'LFTagPolicy': {
                            'CatalogId': source_env['account'],
                            'ResourceType': 'DATABASE',
                            'Expression': [{'TagKey': self.lftag_share.lfTagKey, 'TagValues': [self.lftag_share.lfTagValue]}]
                        }
                    },
                    'Permissions': ['DESCRIBE']
                },
                {
                    'Id': str(uuid.uuid4()),
                    'Principal': {
                        'DataLakePrincipalIdentifier': principalIAMRoleARN
                    },
                    'Resource': {
                        'LFTagPolicy': {
                            'CatalogId': source_env['account'],
                            'ResourceType': 'TABLE',
                            'Expression': [{'TagKey': self.lftag_share.lfTagKey, 'TagValues': [self.lftag_share.lfTagValue]}]
                        }
                    },
                    'Permissions': ['SELECT', 'DESCRIBE'],
                }
            ]
            LakeFormation.batch_revoke_permissions(
                client, source_env['account'], revoke_entries
            )

        return True
