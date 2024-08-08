import logging
from typing import List
from warnings import warn
from datetime import datetime
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.base.aws.quicksight import QuicksightClient
from dataall.modules.shares_base.services.shares_enums import (
    ShareItemHealthStatus,
    ShareItemStatus,
    ShareObjectActions,
    ShareItemActions,
    ShareableType,
)
from dataall.modules.s3_datasets.db.dataset_models import DatasetTable
from dataall.modules.shares_base.services.share_exceptions import PrincipalRoleNotFound
from dataall.modules.s3_datasets_shares.services.share_managers import LFShareManager
from dataall.modules.s3_datasets_shares.aws.ram_client import RamClient
from dataall.modules.shares_base.services.share_object_service import ShareObjectService
from dataall.modules.s3_datasets_shares.services.s3_share_service import S3ShareService
from dataall.modules.shares_base.db.share_object_repositories import ShareObjectRepository
from dataall.modules.shares_base.db.share_state_machines_repositories import ShareStatusRepository
from dataall.modules.s3_datasets_shares.db.s3_share_object_repositories import S3ShareObjectRepository
from dataall.modules.shares_base.db.share_object_state_machines import ShareItemSM
from dataall.modules.s3_datasets_shares.services.share_managers.share_manager_utils import ShareErrorFormatter

from dataall.modules.shares_base.services.sharing_service import ShareData
from dataall.modules.shares_base.services.share_processor_manager import SharesProcessorInterface

log = logging.getLogger(__name__)


class ProcessLakeFormationShare(SharesProcessorInterface):
    def __init__(self, session, share_data, shareable_items, reapply=False):
        self.session = session
        self.share_data: ShareData = share_data
        self.tables: List[DatasetTable] = shareable_items
        self.reapply: bool = reapply

    def _initialize_share_manager(self, tables):
        return LFShareManager(session=self.session, share_data=self.share_data, tables=tables)

    def process_approved_shares(self) -> bool:
        """
        0) Check if source account details are properly initialized and initialize the Glue and LF clients
        1) Grant ALL permissions to pivotRole for source database in source account
        2) Create the shared database in target account if it doesn't exist
        3) Grant permissions to pivotRole and principals to "shared" database
        4) For each shared table:
            a) Update its status to SHARE_IN_PROGRESS with Action Start
            b) Check if table exists on glue catalog raise error if not and flag share item status to failed
            c) If it is a cross-account share:
                c.1) Revoke iamallowedgroups permissions from table
                c.2) Grant target account permissions to original table -> create RAM invitation
                c.3) Accept pending RAM invitation
            d) Create resource link for table in target account
            e) If it is a cross-account share: grant permission to principals to RAM-shared table in target account
            f) grant permission to principals to resource link table
            g) update share item status to SHARE_SUCCESSFUL with Action Success

        Returns
        -------
        True if share is granted successfully
        False if share fails
        """
        log.info('##### Starting Sharing tables #######')
        success = True
        if not self.tables:
            log.info('No tables to share. Skipping...')
        else:
            manager = self._initialize_share_manager(self.tables)
            try:
                if not ShareObjectService.verify_principal_role(self.session, self.share_data.share):
                    raise PrincipalRoleNotFound(
                        'process approved shares',
                        f'Principal role {self.share_data.share.principalRoleName} is not found. Failed to update LF policy',
                    )

                if None in [
                    manager.source_account_id,
                    manager.source_account_region,
                    manager.source_database_name,
                ]:
                    raise Exception(
                        'Source account details not initialized properly. Please check if the catalog account is properly onboarded on data.all'
                    )
                env = EnvironmentService.get_environment_by_uri(self.session, self.share_data.share.environmentUri)
                if EnvironmentService.get_boolean_env_param(self.session, env, 'dashboardsEnabled'):
                    QuicksightClient.check_quicksight_enterprise_subscription(
                        AwsAccountId=env.AwsAccountId, region=env.region
                    )
                manager.initialize_clients()
                manager.grant_pivot_role_all_database_permissions_to_source_database()
                manager.check_if_exists_and_create_shared_database_in_target()
                manager.grant_pivot_role_all_database_permissions_to_shared_database()
                manager.grant_principals_database_permissions_to_shared_database()
            except Exception as e:
                log.error(f'Failed to process approved tables due to {e}')
                manager.handle_share_failure_for_all_tables(
                    tables=self.tables,
                    error=e,
                    share_item_status=ShareItemStatus.Share_Approved.value,
                    reapply=self.reapply,
                )
                return False

            for table in self.tables:
                log.info(f'Sharing table {table.tableUri}/{table.GlueTableName}...')

                share_item = ShareObjectRepository.find_sharable_item(
                    self.session, self.share_data.share.shareUri, table.tableUri
                )

                if not share_item:
                    log.info(
                        f'Share Item not found for {self.share_data.share.shareUri} '
                        f'and Dataset Table {table.GlueTableName} continuing loop...'
                    )
                    continue
                if not self.reapply:
                    shared_item_SM = ShareItemSM(ShareItemStatus.Share_Approved.value)
                    new_state = shared_item_SM.run_transition(ShareObjectActions.Start.value)
                    shared_item_SM.update_state_single_item(self.session, share_item, new_state)

                try:
                    manager.check_table_exists_in_source_database(share_item, table)

                    if manager.cross_account:
                        log.info(f'Processing cross-account permissions for table {table.GlueTableName}...')
                        manager.revoke_iam_allowed_principals_from_table(table)
                        manager.grant_target_account_permissions_to_source_table(table)
                        (
                            retry_share_table,
                            failed_invitations,
                        ) = RamClient.accept_ram_invitation(
                            source_account_id=manager.source_account_id,
                            source_region=manager.source_account_region,
                            source_database=manager.source_database_name,
                            source_table_name=table.GlueTableName,
                            target_account_id=self.share_data.target_environment.AwsAccountId,
                            target_region=self.share_data.target_environment.region,
                        )
                        if retry_share_table:
                            manager.grant_target_account_permissions_to_source_table(table)
                            RamClient.accept_ram_invitation(
                                source_account_id=manager.source_account_id,
                                source_region=manager.source_account_region,
                                source_database=manager.source_database_name,
                                source_table_name=table.GlueTableName,
                                target_account_id=self.share_data.target_environment.AwsAccountId,
                                target_region=self.share_data.target_environment.region,
                            )
                    manager.check_if_exists_and_create_resource_link_table_in_shared_database(table)
                    manager.grant_principals_permissions_to_table_in_target(table)
                    manager.grant_principals_permissions_to_resource_link_table(table)

                    log.info('Attaching TABLE READ permissions...')
                    S3ShareService.attach_dataset_table_read_permission(
                        self.session, self.share_data.share, table.tableUri
                    )

                    if not self.reapply:
                        new_state = shared_item_SM.run_transition(ShareItemActions.Success.value)
                        shared_item_SM.update_state_single_item(self.session, share_item, new_state)
                    ShareStatusRepository.update_share_item_health_status(
                        self.session, share_item, ShareItemHealthStatus.Healthy.value, None, datetime.now()
                    )
                except Exception as e:
                    if not self.reapply:
                        new_state = shared_item_SM.run_transition(ShareItemActions.Failure.value)
                        shared_item_SM.update_state_single_item(self.session, share_item, new_state)
                    else:
                        ShareStatusRepository.update_share_item_health_status(
                            self.session,
                            share_item,
                            ShareItemHealthStatus.Unhealthy.value,
                            str(e),
                            datetime.now(),
                        )
                    success = False
                    manager.handle_share_failure(table=table, error=e)
        return success

    def process_revoked_shares(self) -> bool:
        """
        0) Check if source account details are properly initialized and initialize the Glue and LF clients
        1) Grant Pivot Role all database permissions to the shared database
        2) For each revoked table:
            a) Update its status to REVOKE_IN_PROGRESS with Action Start
            b) Check if table exists on glue catalog raise error if not and flag share item status to failed
            c) Check if resource link table exists in target account
            d) Check if the table is shared in other share requests to this target account
            e) If c is True (resource link table exists), revoke permission to principals to resource link table
            f) If c is True (resource link table exists), revoke permission to principals to table (and for QS Group if no other shares present for table)
            g) If c is True and (old-share or (new-share and d is True, no other shares of this table)) then delete resource link table
            g) If d is True (no other shares of this table with target), revoke permissions to target account to the original table
            h) update share item status to REVOKE_SUCCESSFUL with Action Success
        3) Check if there are existing_shared_tables for this dataset with target environment
        4) If no existing_shared_tables, delete shared database

        Returns
        -------
        True if share is revoked successfully
        False if revoke fails
        """
        log.info('##### Starting Revoking tables #######')
        success = True
        manager = self._initialize_share_manager(self.tables)
        if not self.tables:
            log.info('No tables to revoke. Skipping...')
        else:
            try:
                if None in [
                    manager.source_account_id,
                    manager.source_account_region,
                    manager.source_database_name,
                ]:
                    raise Exception(
                        'Source account details not initialized properly. Please check if the catalog account is properly onboarded on data.all'
                    )
                manager.initialize_clients()
                manager.grant_pivot_role_all_database_permissions_to_shared_database()
            except Exception as e:
                log.error(f'Failed to process revoked tables due to {e}')
                manager.handle_share_failure_for_all_tables(
                    tables=self.tables, error=e, share_item_status=ShareItemStatus.Revoke_Approved.value
                )
                return False

            for table in self.tables:
                log.info(f'Revoking access to table {table.tableUri}/{table.GlueTableName}...')
                share_item = ShareObjectRepository.find_sharable_item(
                    self.session, self.share_data.share.shareUri, table.tableUri
                )

                revoked_item_SM = ShareItemSM(ShareItemStatus.Revoke_Approved.value)
                new_state = revoked_item_SM.run_transition(ShareObjectActions.Start.value)
                revoked_item_SM.update_state_single_item(self.session, share_item, new_state)

                try:
                    log.info(f'Revoking access to table: {table.GlueTableName} ')
                    manager.check_table_exists_in_source_database(share_item, table)

                    log.info('Check resource link table exists')
                    resource_link_table_exists = manager.check_resource_link_table_exists_in_target_database(table)
                    other_table_shares_in_env = (
                        True
                        if S3ShareObjectRepository.check_other_approved_share_item_table_exists(
                            self.session,
                            self.share_data.target_environment.environmentUri,
                            share_item.itemUri,
                            share_item.shareItemUri,
                        )
                        else False
                    )

                    if resource_link_table_exists:
                        log.info('Revoking principal permissions from resource link table')
                        manager.revoke_principals_permissions_to_resource_link_table(table)
                        log.info('Revoking principal permissions from table in target')
                        manager.revoke_principals_permissions_to_table_in_target(table, other_table_shares_in_env)

                        if (manager.is_new_share and not other_table_shares_in_env) or not manager.is_new_share:
                            warn(
                                'share_manager.is_new_share will be deprecated in v2.6.0',
                                DeprecationWarning,
                                stacklevel=2,
                            )
                            manager.grant_pivot_role_drop_permissions_to_resource_link_table(table)
                            manager.delete_resource_link_table_in_shared_database(table)

                    if not other_table_shares_in_env:
                        manager.revoke_external_account_access_on_source_account(table)

                    if (
                        self.share_data.share.groupUri != self.share_data.dataset.SamlAdminGroupName
                        and self.share_data.share.groupUri != self.share_data.dataset.stewards
                    ):
                        log.info('Deleting TABLE READ permissions...')
                        S3ShareService.delete_dataset_table_read_permission(
                            self.session, self.share_data.share, table.tableUri
                        )

                    new_state = revoked_item_SM.run_transition(ShareItemActions.Success.value)
                    revoked_item_SM.update_state_single_item(self.session, share_item, new_state)

                    ShareStatusRepository.update_share_item_health_status(
                        self.session, share_item, None, None, share_item.lastVerificationTime
                    )

                except Exception as e:
                    new_state = revoked_item_SM.run_transition(ShareItemActions.Failure.value)
                    revoked_item_SM.update_state_single_item(self.session, share_item, new_state)
                    success = False

                    manager.handle_revoke_failure(table=table, error=e)

            try:
                if self.tables:
                    existing_shared_tables_in_share = S3ShareObjectRepository.check_existing_shared_items_of_type(
                        session=self.session, uri=self.share_data.share.shareUri, item_type=ShareableType.Table.value
                    )
                    log.info(f'Remaining tables shared in this share object = {existing_shared_tables_in_share}')

                    if not existing_shared_tables_in_share:
                        log.info('Revoking permissions to target shared database...')
                        manager.revoke_principals_database_permissions_to_shared_database()

                        if not manager.is_new_share:
                            log.info('Deleting OLD target shared database...')
                            warn(
                                'share_manager.is_new_share will be deprecated in v2.6.0',
                                DeprecationWarning,
                                stacklevel=2,
                            )
                            manager.delete_shared_database_in_target()

                    existing_shares_with_shared_tables_in_environment = (
                        S3ShareObjectRepository.list_shares_with_existing_shared_items_in_environment(
                            session=self.session,
                            dataset_uri=self.share_data.dataset.datasetUri,
                            environment_uri=self.share_data.target_environment.environmentUri,
                            item_type=ShareableType.Table.value,
                        )
                    )
                    warn(
                        'S3ShareObjectRepository.list_shares_with_existing_shared_items_in_environment will be deprecated in v2.6.0',
                        DeprecationWarning,
                        stacklevel=2,
                    )
                    existing_old_shares_bool = [
                        manager.glue_client_in_target.database_exists(item['databaseName'])
                        for item in existing_shares_with_shared_tables_in_environment
                    ]
                    log.info(
                        f'Remaining tables shared from this dataset to this environment = {existing_shares_with_shared_tables_in_environment}, {existing_old_shares_bool}'
                    )
                    if manager.is_new_share and False not in existing_old_shares_bool:
                        log.info('Deleting target shared database...')
                        warn(
                            'share_manager.is_new_share will be deprecated in v2.6.0', DeprecationWarning, stacklevel=2
                        )
                        manager.delete_shared_database_in_target()
            except Exception as e:
                log.error(
                    f'Failed to clean-up database permissions or delete shared database {manager.shared_db_name} '
                    f'due to: {e}'
                )
                success = False
            return success

    def verify_shares(self) -> bool:
        log.info('##### Verifying tables #######')
        if not self.tables:
            log.info('No tables to verify. Skipping...')
        else:
            manager = self._initialize_share_manager(self.tables)
            try:
                if None in [
                    manager.source_account_id,
                    manager.source_account_region,
                    manager.source_database_name,
                ]:
                    raise Exception(
                        'Source account details not initialized properly. Please check if the catalog account is properly onboarded on data.all'
                    )
                manager.initialize_clients()
                if not manager.check_pivot_role_permissions_to_source_database():
                    manager.grant_pivot_role_all_database_permissions_to_source_database()
                shared_database_exists = manager.check_shared_database_in_target()
                if shared_database_exists and not manager.check_pivot_role_permissions_to_shared_database():
                    manager.grant_pivot_role_all_database_permissions_to_shared_database()
                manager.check_principals_permissions_to_shared_database()
            except Exception as e:
                manager.db_level_errors = [str(e)]

            for table in self.tables:
                log.info(f'Verifying access to table {table.tableUri}/{table.GlueTableName}...')
                try:
                    share_item = ShareObjectRepository.find_sharable_item(
                        self.session, self.share_data.share.shareUri, table.tableUri
                    )
                    manager.verify_table_exists_in_source_database(share_item, table)

                    if manager.cross_account:
                        manager.check_target_account_permissions_to_source_table(table)

                        if not RamClient.check_ram_invitation_status(
                            source_account_id=manager.source_account_id,
                            source_region=manager.source_account_region,
                            target_account_id=self.share_data.target_environment.AwsAccountId,
                            source_database=manager.source_database_name,
                            source_table_name=table.GlueTableName,
                        ):
                            manager.tbl_level_errors.append(
                                ShareErrorFormatter.missing_permission_error_msg(
                                    self.share_data.target_environment.AwsAccountId,
                                    'RAM Invitation',
                                    'ASSOCIATED',
                                    'Glue Table',
                                    f'{manager.source_database_name}.{table.GlueTableName}',
                                )
                            )

                    manager.verify_resource_link_table_exists_in_target_database(table)
                    manager.check_principals_permissions_to_table_in_target(table)
                    manager.check_principals_permissions_to_resource_link_table(table)

                except Exception as e:
                    manager.tbl_level_errors = [str(e)]

                if len(manager.db_level_errors) or len(manager.tbl_level_errors):
                    ShareStatusRepository.update_share_item_health_status(
                        self.session,
                        share_item,
                        ShareItemHealthStatus.Unhealthy.value,
                        ' | '.join(manager.db_level_errors) + ' | ' + ' | '.join(manager.tbl_level_errors),
                        datetime.now(),
                    )
                else:
                    ShareStatusRepository.update_share_item_health_status(
                        self.session, share_item, ShareItemHealthStatus.Healthy.value, None, datetime.now()
                    )
        return True
