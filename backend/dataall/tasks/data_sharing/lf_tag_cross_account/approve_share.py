import logging
import time

from botocore.exceptions import ClientError

from ..common.lf_share_approval import LFShareApproval
from ....aws.handlers.lakeformation import LakeFormation
from ....aws.handlers.ram import Ram
from ....aws.handlers.sts import SessionHelper
from ....db import models, api
from ....aws.handlers.glue import Glue

log = logging.getLogger(__name__)


class LFTagShareApproval:
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

    def approve_share(
        self,
    ) -> bool:
        """
        1) Create LF Tag in Consumer Account (if not exist already)
        2) Grant Consumer LF Tag Permissions (if not already)
        2) Retrieve All Data Objects with LF Tag Key Value
        3) For Each Data Object (i.e. DB, Table, Column)

            1) Grant LF-tag permissions to the consumer account. --> FROM PRODUCER ACCT
            2) Grant data permissions to the consumer account.  --> FROM PRODUCER ACCT
            3) Optionally, revoke permissions for IAMAllowedPrincipals on the database, tables, and columns.
            4) Create a resource link to the shared table. 
            5) Assign LF-Tag to the target database.

        Parameters
        ----------


        Returns
        -------
        True if approve succeeds
        """

        principalIAMRoleARN = f"arn:aws:iam::{self.target_environment.AwsAccountId}:role/{self.lftag_share.principalIAMRoleName}"
        for source_env in self.source_env_list:
            LakeFormation.grant_lftag_data_permissions_to_principal(
                source_acct=source_env['account'],
                source_region=source_env['region'],
                principal=principalIAMRoleARN,
                tag_name=self.lftag_share.lfTagKey,
                tag_values=[self.lftag_share.lfTagValue],
                permissionsWithGrant=False
            )
            log.info("EXTERNAL ACCT DATA PERMISSIONS GRANTED IN SOURCE ENV FOR SOURCE TAG")

            # Accept RAM Invites For Each Source Different From Target
            if source_env['account'] != self.target_environment.AwsAccountId:
                Ram.accept_lftag_ram_invitation(source_env, self.target_environment, principalIAMRoleARN)

        # For Each Dataset (Glue DB)
        for db in self.tagged_datasets:
            if db.AwsAccountId != self.target_environment.AwsAccountId:
                shared_db_name = (db.GlueDatabaseName + '_shared_' + self.lftag_share.lftagShareUri)[:254]

                # Create a resource link to the shared table
                self.create_lftag_resource_link_db(db, self.target_environment, principalIAMRoleARN, shared_db_name)
                log.info("RESOURCE LINK CREATED")
            
        # For Each Data Table
        for table in self.tagged_tables:
            if table.AWSAccountId != self.target_environment.AwsAccountId:
                shared_db_name = (table.GlueDatabaseName + '_shared_' + self.lftag_share.lftagShareUri)[:254]
                data = self.build_lftag_share_data(self.target_environment, [principalIAMRoleARN], table, shared_db_name)
                
                # Create Shared DB if not Exist Already
                log.info(
                    f'Creating shared db ...'
                    f'{self.target_environment.AwsAccountId}://{shared_db_name}'
                )

                database = Glue.create_database(
                    self.target_environment.AwsAccountId,
                    shared_db_name,
                    self.target_environment.region,
                    f's3://{table.S3BucketName}',
                    principalIAMRoleARN=principalIAMRoleARN
                )
                log.info("SHARED DB CREATED")

                # Create a resource link to the shared table
                self.create_lftag_resource_link(data, principalIAMRoleARN)
                log.info("RESOURCE LINK CREATED")

        for col in self.tagged_columns:
            if col.AWSAccountId != self.target_environment.AwsAccountId:
                shared_db_name = (col.GlueDatabaseName + '_shared_' + self.lftag_share.lftagShareUri)[:254]
                data = self.build_lftag_share_data(self.target_environment, [principalIAMRoleARN], col, shared_db_name)
                
                # Create Shared DB if not Exist Already
                log.info(
                    f'Creating shared db ...'
                    f'{self.target_environment.AwsAccountId}://{shared_db_name}'
                )
                
                col_table = api.DatasetTable.get_dataset_table_by_uri(self.session, col.tableUri)

                database = Glue.create_database(
                    self.target_environment.AwsAccountId,
                    shared_db_name,
                    self.target_environment.region,
                    f's3://{col_table.S3BucketName}',
                    principalIAMRoleARN=principalIAMRoleARN
                )
                log.info("SHARED DB CREATED")

                # Create a resource link to the shared table
                self.create_lftag_resource_link(data, principalIAMRoleARN)
                log.info("RESOURCE LINK CREATED")

        return True

    @staticmethod
    def create_lftag_resource_link(data, principalIAMRoleARN) -> dict:
        """
        Creates a resource link to the source shared Glue table
        Parameters
        ----------
        data : data of source and target accounts

        Returns
        -------
        boto3 creation response
        """
        source = data['source']
        target = data['target']

        target_database = target['database']
        resource_link_input = {
            'Name': source['tablename'],
            'TargetTable': {
                'CatalogId': data['source']['accountid'],
                'DatabaseName': source['database'],
                'Name': source['tablename'],
            },
        }

        try:
            resource_link = Glue.create_resource_link(
                accountid=target['accountid'],
                region=target['region'],
                database=target_database,
                resource_link_name=source['tablename'],
                resource_link_input=resource_link_input,
                principalRoleArn=principalIAMRoleARN
            )

            return resource_link

        except ClientError as e:
            log.warning(
                f'Resource Link {resource_link_input} was not created due to: {e}'
            )
            raise e

    @staticmethod
    def create_lftag_resource_link_db(db, target_env, principalIAMRoleARN, shared_db_name) -> dict:
        """
        Creates a resource link to the source shared Glue Database
        Parameters
        ----------
        data : data of source and target accounts

        Returns
        -------
        boto3 creation response
        """
        resource_link_input = {
            'Name': shared_db_name,
            'TargetDatabase': {
                'CatalogId': db.AwsAccountId,
                'DatabaseName': db.GlueDatabaseName,
            },
        }

        try:
            resource_link = Glue.create_resource_link_db(
                accountid=target_env.AwsAccountId,
                region=target_env.region,
                database=shared_db_name,
                resource_link_name=shared_db_name,
                resource_link_input=resource_link_input,
                principalRoleArn=principalIAMRoleARN
            )

            return resource_link

        except ClientError as e:
            log.warning(
                f'Resource Link {resource_link_input} was not created due to: {e}'
            )
            raise e

    @staticmethod
    def build_lftag_share_data(target_environment, principals, table, shared_db_name) -> dict:
        """
        Build aws dict for boto3 operations on Glue and LF from share data
        Parameters
        ----------
        principals : team role
        table : dataset table

        Returns
        -------
        dict for boto3 operations
        """
        data = {
            'source': {
                'accountid': table.AWSAccountId,
                'region': table.region,
                'database': table.GlueDatabaseName,
                'tablename': table.GlueTableName,
            },
            'target': {
                'accountid': target_environment.AwsAccountId,
                'region': target_environment.region,
                'principals': principals,
                'database': shared_db_name,
            },
        }
        return data

        # Create LF Tag in Consumer Account (if not exist already)
        # lf_client = LakeFormation.create_lf_client(target_environment.AwsAccountId, target_environment.region)
        # # LakeFormation.create_or_update_lf_tag(
        # #     accountid=target_environment.AwsAccountId,
        # #     lf_client=lf_client,
        # #     tag_name=lftag_share.lfTagKey,
        # #     tag_values=[lftag_share.lfTagValue]
        # # )
        # # log.info("TAG CREATED IN TARGET ENV")

        # # # Grant Consumer LF Tag Permissions (if not already)
        # # LakeFormation.grant_lftag_data_permissions_to_principal(
        # #     source_acct=target_environment.AwsAccountId,
        # #     source_region=target_environment.region,
        # #     principal=lftag_share.principalIAMRoleName,
        # #     tag_name=lftag_share.lfTagKey,
        # #     tag_values=[lftag_share.lfTagValue],
        # #     iamRole=True
        # # )
        # # log.info("PERMISSIONS GRANTED IN TARGET ENV FOR TARGET TAG")

        # For Each Source Env -
        # - Ensure V3 of LF Data Catalog Settings for Source and Target
        # - Revoke Permissions for IAMAllowedPrincipals on the DB, Tables, and Columns
        # - Grant LF Tag Permissions (only DESCRIBE to Consumer IAM ROLE with NO GRANTABLE)
        # - Grant LF Tag DATA Permissions (DESCRIBE DB and SELECT DESCRIBE Table to Consumer IAM ROLE with NO GRANTABLE)

        #  For Each Source Env
            # MAY NOT NEED
            # LakeFormation.grant_lftag_permissions_to_external_acct(
            #     source_acct=source_env['account'],
            #     source_region=source_env['region'],
            #     principal=principalIAMRoleARN,
            #     tag_name=lftag_share.lfTagKey,
            #     tag_values=[lftag_share.lfTagValue],
            #     permissions=["DESCRIBE"]
            # )
            # log.info("EXTERNAL IAM Role LF TAG PERMISSIONS GRANTED IN SOURCE ENV FOR SOURCE TAG")


        # For Each Data Table Column
            
            # Grant LF-tag permissions to the consumer account
            # LakeFormation.grant_lftag_permissions_to_external_acct(
            #     source_acct=table.AWSAccountId,
            #     source_region=table.region,
            #     external_acct=target_environment.AwsAccountId,
            #     tag_name=lftag_share.lfTagKey,
            #     tag_values=[lftag_share.lfTagValue],
            #     permissions=["DESCRIBE"]
            # )
            # LakeFormation.grant_lftag_permissions_to_external_acct(
            #     source_acct=table.AWSAccountId,
            #     source_region=table.region,
            #     principal=f"arn:aws:iam::{table.AWSAccountId}:role/{lftag_share.principalIAMRoleName}",
            #     tag_name=lftag_share.lfTagKey,
            #     tag_values=[lftag_share.lfTagValue],
            #     permissions=["DESCRIBE"]
            # )
            # log.info("EXTERNAL ACCT LF TAG PERMISSIONS GRANTED IN SOURCE ENV FOR SOURCE TAG")

            # Grant data permissions to the consumer account
            # LakeFormation.grant_lftag_data_permissions_to_principal(
            #     source_acct=table.AWSAccountId,
            #     source_region=table.region,
            #     principal=target_environment.AwsAccountId,
            #     tag_name=lftag_share.lfTagKey,
            #     tag_values=[lftag_share.lfTagValue],
            #     iamRole=False,
            #     permissionsWithGrant=True
            # )
            # LakeFormation.grant_lftag_data_permissions_to_principal(
            #     source_acct=table.AWSAccountId,
            #     source_region=table.region,
            #     principal=lftag_share.principalIAMRoleName,
            #     tag_name=lftag_share.lfTagKey,
            #     tag_values=[lftag_share.lfTagValue],
            #     iamRole=True,
            #     permissionsWithGrant=True
            # )
            # log.info("EXTERNAL ACCT DATA PERMISSIONS GRANTED IN SOURCE ENV FOR SOURCE TAG")

            # Create Shared DB if not Exist Already
            # log.info(
            #     f'Creating shared db ...'
            #     f'{target_environment.AwsAccountId}://{shared_db_name}'
            # )

            # database = Glue.create_database(
            #     target_environment.AwsAccountId,
            #     shared_db_name,
            #     target_environment.region,
            #     f's3://{table.S3BucketName}',
            # )
            # log.info("SHARED DB CREATED")

            # LakeFormation.grant_pivot_role_all_database_permissions(
            #     target_environment.AwsAccountId, target_environment.region, shared_db_name
            # )

            # # Build Dict of Data For Source and Target 
            # principals = [f"arn:aws:iam::{target_environment.AwsAccountId}:role/{lftag_share.principalIAMRoleName}"]
            # data = DataSharingService.build_lftag_share_data(target_environment, principals, table, shared_db_name)
            
            # # Revoke IAM Allowed Groups
            # source_lf_client = LakeFormation.create_lf_client(table.AWSAccountId, table.region)
            
            # LakeFormation.revoke_iamallowedgroups_super_permission_from_table(
            #     source_lf_client,
            #     data['source']['accountid'],
            #     data['source']['database'],
            #     data['source']['tablename'],
            # )

            # # Create a resource link to the shared table
            # DataSharingService.create_lftag_resource_link(data)
            # log.info("RESOURCE LINK CREATED")

            # # Assign LF-Tag to the target database
            # lf_client.add_lf_tags_to_resource(
            #     CatalogId=target_environment.AwsAccountId,
            #     Resource={
            #         'Table': {
            #             'CatalogId': target_environment.AwsAccountId,
            #             'DatabaseName': shared_db_name,
            #             'Name': table.GlueTableName,
            #         }
            #     },
            #     LFTags=[
            #         {
            #             'CatalogId': target_environment.AwsAccountId,
            #             'TagKey': lftag_share.lfTagKey,
            #             'TagValues': [lftag_share.lfTagValue]
            #         },
            #     ]
            # )
            # log.info("TAG ASSIGNED TO SHARED TABLE")