import logging
import os

from .share_processors.lf_process_cross_account_share import ProcessLFCrossAccountShare
from .share_processors.lf_process_same_account_share import ProcessLFSameAccountShare
from .share_processors.s3_process_share import ProcessS3Share

from ...aws.handlers.glue import Glue
from ...aws.handlers.lakeformation import LakeFormation
from ...aws.handlers.ram import Ram
from ...aws.handlers.sts import SessionHelper
from ...db import api, models, Engine
from ...utils import Parameter
from botocore.exceptions import ClientError

log = logging.getLogger(__name__)

REFRESH_SHARES_STATES = [
    models.ShareObjectStatus.Approved.value,
    models.ShareObjectStatus.Revoked.value,
]


class DataSharingService:
    def __init__(self):
        pass

    @classmethod
    def approve_lftag_share(cls, engine: Engine, lftag_share_uri: str) -> bool:
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
        engine : db.engine
        lftag_share_uri : lftag share uri

        Returns
        -------
        True if approve succeeds
        """
        with engine.scoped_session() as session:
            
            """
            Need
            1 - Set of All Source Environments with Tag
            2 - All Datasets (DBs) Tagged with Tag Key, Value
            3 - All Tables Tagged with Tag Key, Value
            4 - All Columns Tagged with Tag Key, Value
            5 - Target Environment
            """
            (
                source_env_list,
                tagged_datasets,
                tagged_tables,
                tagged_columns,
                lftag_share,
                target_environment
            ) = api.ShareObject.get_lftag_share_data(session, lftag_share_uri)

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
        principalIAMRoleARN = f"arn:aws:iam::{target_environment.AwsAccountId}:role/{lftag_share.principalIAMRoleName}"
        for source_env in source_env_list:
            LakeFormation.grant_lftag_permissions_to_external_acct(
                source_acct=source_env['account'],
                source_region=source_env['region'],
                principal=principalIAMRoleARN,
                tag_name=lftag_share.lfTagKey,
                tag_values=[lftag_share.lfTagValue],
                permissions=["DESCRIBE"]
            )
            log.info("EXTERNAL IAM Role LF TAG PERMISSIONS GRANTED IN SOURCE ENV FOR SOURCE TAG")

            LakeFormation.grant_lftag_data_permissions_to_principal(
                source_acct=source_env['account'],
                source_region=source_env['region'],
                principal=principalIAMRoleARN,
                tag_name=lftag_share.lfTagKey,
                tag_values=[lftag_share.lfTagValue],
                permissionsWithGrant=False
            )
            log.info("EXTERNAL ACCT DATA PERMISSIONS GRANTED IN SOURCE ENV FOR SOURCE TAG")

            # Accept RAM Invites For Each
            Ram.accept_lftag_ram_invitation(source_env, target_environment, principalIAMRoleARN)

        # For Each Dataset (Glue DB)
        for db in tagged_datasets:
            shared_db_name = (db.GlueDatabaseName + '_shared_' + lftag_share_uri)[:254]

            # Create a resource link to the shared table
            DataSharingService.create_lftag_resource_link_db(db, target_environment, principalIAMRoleARN, shared_db_name)
            log.info("RESOURCE LINK CREATED")
            
        # For Each Data Table
        for table in tagged_tables:
            shared_db_name = (table.GlueDatabaseName + '_shared_' + lftag_share_uri)[:254]
            data = DataSharingService.build_lftag_share_data(target_environment, [principalIAMRoleARN], table, shared_db_name)
            
            # Create Shared DB if not Exist Already
            log.info(
                f'Creating shared db ...'
                f'{target_environment.AwsAccountId}://{shared_db_name}'
            )

            database = Glue.create_database(
                target_environment.AwsAccountId,
                shared_db_name,
                target_environment.region,
                f's3://{table.S3BucketName}',
            )
            log.info("SHARED DB CREATED")

            # Create a resource link to the shared table
            DataSharingService.create_lftag_resource_link(data, principalIAMRoleARN)
            log.info("RESOURCE LINK CREATED")

        for col in tagged_columns:
            shared_db_name = (col.GlueDatabaseName + '_shared_' + lftag_share_uri)[:254]
            data = DataSharingService.build_lftag_share_data(target_environment, [principalIAMRoleARN], col, shared_db_name)
            
            # Create Shared DB if not Exist Already
            log.info(
                f'Creating shared db ...'
                f'{target_environment.AwsAccountId}://{shared_db_name}'
            )
            
            with engine.scoped_session() as session:
                col_table = api.DatasetTable.get_dataset_table_by_uri(session, col.tableUri)

            database = Glue.create_database(
                target_environment.AwsAccountId,
                shared_db_name,
                target_environment.region,
                f's3://{col_table.S3BucketName}',
            )
            log.info("SHARED DB CREATED")

            # Create a resource link to the shared table
            DataSharingService.create_lftag_resource_link(data)
            log.info("RESOURCE LINK CREATED")

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

    @classmethod
    def reject_lftag_share(cls, engine: Engine, share_uri: str) -> bool:
        return True

    @classmethod
    def approve_share(cls, engine: Engine, share_uri: str) -> bool:
        """
        1) Updates share object State Machine with the Action: Start
        2) Retrieves share data and items in Share_Approved state
        3) Calls sharing folders processor to grant share
        4) Calls sharing tables processor for same or cross account sharing to grant share
        5) Updates share object State Machine with the Action: Finish

        Parameters
        ----------
        engine : db.engine
        share_uri : share uri

        Returns
        -------
        True if sharing succeeds,
        False if folder or table sharing failed
        """
        with engine.scoped_session() as session:
            (
                source_env_group,
                env_group,
                dataset,
                share,
                source_environment,
                target_environment,
            ) = api.ShareObject.get_share_data(session, share_uri)

            Share_SM = api.ShareObjectSM(share.status)
            new_share_state = Share_SM.run_transition(models.Enums.ShareObjectActions.Start.value)
            Share_SM.update_state(session, share, new_share_state)

            (
                shared_tables,
                shared_folders
            ) = api.ShareObject.get_share_data_items(session, share_uri, models.ShareItemStatus.Share_Approved.value)

        log.info(f'Granting permissions to folders: {shared_folders}')

        approved_folders_succeed = ProcessS3Share.process_approved_shares(
            session,
            dataset,
            share,
            shared_folders,
            source_environment,
            target_environment,
            source_env_group,
            env_group
        )
        log.info(f'sharing folders succeeded = {approved_folders_succeed}')

        if source_environment.AwsAccountId != target_environment.AwsAccountId:
            processor = ProcessLFCrossAccountShare(
                session,
                dataset,
                share,
                shared_tables,
                [],
                source_environment,
                target_environment,
                env_group,
            )
        else:
            processor = ProcessLFSameAccountShare(
                session,
                dataset,
                share,
                shared_tables,
                [],
                source_environment,
                target_environment,
                env_group
            )

        log.info(f'Granting permissions to tables: {shared_tables}')
        approved_tables_succeed = processor.process_approved_shares()
        log.info(f'sharing tables succeeded = {approved_tables_succeed}')

        new_share_state = Share_SM.run_transition(models.Enums.ShareObjectActions.Finish.value)
        Share_SM.update_state(session, share, new_share_state)

        return approved_tables_succeed if approved_folders_succeed else False

    @classmethod
    def revoke_share(cls, engine: Engine, share_uri: str):
        """
        1) Updates share object State Machine with the Action: Start
        2) Retrieves share data and items in Revoke_Approved state
        3) Calls sharing folders processor to revoke share
        4) Checks if remaining folders are shared and effectuates clean up with folders processor
        5) Calls sharing tables processor for same or cross account sharing to revoke share
        6) Checks if remaining tables are shared and effectuates clean up with tables processor
        7) Updates share object State Machine with the Action: Finish

        Parameters
        ----------
        engine : db.engine
        share_uri : share uri

        Returns
        -------
        True if revoke succeeds
        False if folder or table revoking failed
        """

        with engine.scoped_session() as session:
            (
                source_env_group,
                env_group,
                dataset,
                share,
                source_environment,
                target_environment,
            ) = api.ShareObject.get_share_data(session, share_uri)

            Share_SM = api.ShareObjectSM(share.status)
            new_share_state = Share_SM.run_transition(models.Enums.ShareObjectActions.Start.value)
            Share_SM.update_state(session, share, new_share_state)

            revoked_item_SM = api.ShareItemSM(models.ShareItemStatus.Revoke_Approved.value)

            (
                revoked_tables,
                revoked_folders
            ) = api.ShareObject.get_share_data_items(session, share_uri, models.ShareItemStatus.Revoke_Approved.value)

            new_state = revoked_item_SM.run_transition(models.ShareObjectActions.Start.value)
            revoked_item_SM.update_state(session, share_uri, new_state)

            log.info(f'Revoking permissions to folders: {revoked_folders}')

            revoked_folders_succeed = ProcessS3Share.process_revoked_shares(
                session,
                dataset,
                share,
                revoked_folders,
                source_environment,
                target_environment,
                source_env_group,
                env_group,
            )
            log.info(f'revoking folders succeeded = {revoked_folders_succeed}')
            existing_shared_items = api.ShareObject.check_existing_shared_items_of_type(
                session,
                share_uri,
                models.ShareableType.StorageLocation.value
            )
            log.info(f'Still remaining S3 resources shared = {existing_shared_items}')
            if not existing_shared_items and revoked_folders:
                log.info("Clean up S3 access points...")
                clean_up_folders = ProcessS3Share.clean_up_share(
                    dataset=dataset,
                    share=share,
                    target_environment=target_environment
                )
                log.info(f"Clean up S3 successful = {clean_up_folders}")

            if source_environment.AwsAccountId != target_environment.AwsAccountId:
                processor = ProcessLFCrossAccountShare(
                    session,
                    dataset,
                    share,
                    [],
                    revoked_tables,
                    source_environment,
                    target_environment,
                    env_group,
                )
            else:
                processor = ProcessLFSameAccountShare(
                    session,
                    dataset,
                    share,
                    [],
                    revoked_tables,
                    source_environment,
                    target_environment,
                    env_group)

            log.info(f'Revoking permissions to tables: {revoked_tables}')
            revoked_tables_succeed = processor.process_revoked_shares()
            log.info(f'revoking tables succeeded = {revoked_tables_succeed}')

            existing_shared_items = api.ShareObject.check_existing_shared_items_of_type(
                session,
                share_uri,
                models.ShareableType.Table.value
            )
            log.info(f'Still remaining LF resources shared = {existing_shared_items}')
            if not existing_shared_items and revoked_tables:
                log.info("Clean up LF remaining resources...")
                clean_up_tables = processor.clean_up_share()
                log.info(f"Clean up LF successful = {clean_up_tables}")

            existing_pending_items = api.ShareObject.check_pending_share_items(session, share_uri)
            if existing_pending_items:
                new_share_state = Share_SM.run_transition(models.Enums.ShareObjectActions.FinishPending.value)
            else:
                new_share_state = Share_SM.run_transition(models.Enums.ShareObjectActions.Finish.value)
            Share_SM.update_state(session, share, new_share_state)

            return revoked_tables_succeed and revoked_folders_succeed

    @classmethod
    def clean_lfv1_ram_resources(cls, environment: models.Environment):
        """
        Deletes LFV1 resource shares for an environment
        Parameters
        ----------
        environment : models.Environment

        Returns
        -------
        None
        """
        return Ram.delete_lakeformation_v1_resource_shares(
            SessionHelper.remote_session(accountid=environment.AwsAccountId).client(
                'ram', region_name=environment.region
            )
        )

    @classmethod
    def refresh_shares(cls, engine: Engine) -> bool:
        """
        Refreshes the shares at scheduled frequency.
        If a share is in 'Approve' state it triggers an approve ECS sharing task
        If a share is in 'Revoked' state it triggers a revoke ECS sharing task
        Also cleans up LFV1 ram resource shares if enabled on SSM
        Parameters
        ----------
        engine : db.engine

        Returns
        -------
        true if refresh succeeds
        """
        share_object_refreshable_states = api.ShareObjectSM.get_share_object_refreshable_states()
        with engine.scoped_session() as session:
            environments = session.query(models.Environment).all()
            shares = (
                session.query(models.ShareObject)
                .filter(models.ShareObject.status.in_(REFRESH_SHARES_STATES))
                .all()
            )

        # Feature toggle: default value is False
        if (
            Parameter().get_parameter(
                os.getenv('envname', 'local'), 'shares/cleanlfv1ram'
            )
            == 'True'
        ):
            log.info('LFV1 Cleanup toggle is enabled')
            for e in environments:
                log.info(
                    f'Cleaning LFV1 ram resource for environment: {e.AwsAccountId}/{e.region}...'
                )
                cls.clean_lfv1_ram_resources(e)

        if not shares:
            log.info('No Approved nor Revoked shares found. Nothing to do...')
            return True

        for share in shares:
            try:
                log.info(
                    f'Refreshing share {share.shareUri} with {share.status} status...'
                )
                if share.status in [models.ShareObjectStatus.Approved.value]:
                    cls.approve_share(engine, share.shareUri)
                else:
                    cls.revoke_share(engine, share.shareUri)

            except Exception as e:
                log.error(
                    f'Failed refreshing share {share.shareUri} with {share.status}. '
                    f'due to: {e}'
                )
        return True
