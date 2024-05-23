import logging
from typing import List
from warnings import warn
from datetime import datetime
from dataall.core.environment.db.environment_models import Environment, EnvironmentGroup
from dataall.modules.shares_base.services.shares_enums import (
    ShareItemHealthStatus,
    ShareItemStatus,
    ShareObjectActions,
    ShareItemActions,
    ShareableType,
)
from dataall.modules.s3_datasets_shares.services.share_exceptions import PrincipalRoleNotFound
from dataall.modules.s3_datasets_shares.services.share_managers import LFShareManager
from dataall.modules.s3_datasets_shares.aws.ram_client import RamClient
from dataall.modules.s3_datasets_shares.services.share_object_service import ShareObjectService
from dataall.modules.s3_datasets_shares.db.share_object_repositories import ShareObjectRepository
from dataall.modules.shares_base.db.share_object_state_machines import ShareItemSM
from dataall.modules.s3_datasets_shares.services.share_managers.share_manager_utils import ShareErrorFormatter

from dataall.modules.shares_base.services.sharing_service import SharesProcessorInterface

log = logging.getLogger(__name__)


class ProcessLakeFormationShare(SharesProcessorInterface):
    @staticmethod
    def initialize_share_managers(
        session, dataset, share, items, source_environment, target_environment, env_group, reapply
    ) -> List[LFShareManager]:
        return [LFShareManager(
            session, dataset, share, items, source_environment, target_environment, env_group, reapply
        )]

    @staticmethod
    def process_approved_shares(share_managers: List[LFShareManager]) -> bool:
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
        share_manager = share_managers[0]
        log.info('##### Starting Sharing tables #######')
        success = True
        if not share_manager.tables:
            log.info('No tables to share. Skipping...')
        else:
            try:
                if not ShareObjectService.verify_principal_role(share_manager.session, share_manager.share):
                    raise PrincipalRoleNotFound(
                        'process approved shares',
                        f'Principal role {share_manager.share.principalIAMRoleName} is not found. Failed to update LF policy',
                    )

                if None in [
                    share_manager.source_account_id,
                    share_manager.source_account_region,
                    share_manager.source_database_name,
                ]:
                    raise Exception(
                        'Source account details not initialized properly. Please check if the catalog account is properly onboarded on data.all'
                    )
                share_manager.initialize_clients()
                share_manager.grant_pivot_role_all_database_permissions_to_source_database()
                share_manager.check_if_exists_and_create_shared_database_in_target()
                share_manager.grant_pivot_role_all_database_permissions_to_shared_database()
                share_manager.grant_principals_database_permissions_to_shared_database()
            except Exception as e:
                log.error(f'Failed to process approved tables due to {e}')
                share_manager.handle_share_failure_for_all_tables(
                    tables=share_manager.tables,
                    error=e,
                    share_item_status=ShareItemStatus.Share_Approved.value,
                    reapply=share_manager.reapply,
                )
                return False

            for table in share_manager.tables:
                log.info(f'Sharing table {table.GlueTableName}...')

                share_item = ShareObjectRepository.find_sharable_item(
                    share_manager.session, share_manager.share.shareUri, table.tableUri
                )

                if not share_item:
                    log.info(
                        f'Share Item not found for {share_manager.share.shareUri} '
                        f'and Dataset Table {table.GlueTableName} continuing loop...'
                    )
                    continue
                if not share_manager.reapply:
                    shared_item_SM = ShareItemSM(ShareItemStatus.Share_Approved.value)
                    new_state = shared_item_SM.run_transition(ShareObjectActions.Start.value)
                    shared_item_SM.update_state_single_item(share_manager.session, share_item, new_state)

                try:
                    share_manager.check_table_exists_in_source_database(share_item, table)

                    if share_manager.cross_account:
                        log.info(f'Processing cross-account permissions for table {table.GlueTableName}...')
                        share_manager.revoke_iam_allowed_principals_from_table(table)
                        share_manager.grant_target_account_permissions_to_source_table(table)
                        (
                            retry_share_table,
                            failed_invitations,
                        ) = RamClient.accept_ram_invitation(
                            source_account_id=share_manager.source_account_id,
                            source_region=share_manager.source_account_region,
                            source_database=share_manager.source_database_name,
                            source_table_name=table.GlueTableName,
                            target_account_id=share_manager.target_environment.AwsAccountId,
                            target_region=share_manager.target_environment.region,
                        )
                        if retry_share_table:
                            share_manager.grant_target_account_permissions_to_source_table(table)
                            RamClient.accept_ram_invitation(
                                source_account_id=share_manager.source_account_id,
                                source_region=share_manager.source_account_region,
                                source_database=share_manager.source_database_name,
                                source_table_name=table.GlueTableName,
                                target_account_id=share_manager.target_environment.AwsAccountId,
                                target_region=share_manager.target_environment.region,
                            )
                    share_manager.check_if_exists_and_create_resource_link_table_in_shared_database(table)
                    share_manager.grant_principals_permissions_to_table_in_target(table)
                    share_manager.grant_principals_permissions_to_resource_link_table(table)
                    if not share_manager.reapply:
                        new_state = shared_item_SM.run_transition(ShareItemActions.Success.value)
                        shared_item_SM.update_state_single_item(share_manager.session, share_item, new_state)
                    ShareObjectRepository.update_share_item_health_status(
                        share_manager.session, share_item, ShareItemHealthStatus.Healthy.value, None, datetime.now()
                    )
                except Exception as e:
                    if not share_manager.reapply:
                        new_state = shared_item_SM.run_transition(ShareItemActions.Failure.value)
                        shared_item_SM.update_state_single_item(share_manager.session, share_item, new_state)
                    else:
                        ShareObjectRepository.update_share_item_health_status(
                            share_manager.session,
                            share_item,
                            ShareItemHealthStatus.Unhealthy.value,
                            str(e),
                            datetime.now(),
                        )
                    success = False
                    share_manager.handle_share_failure(table=table, error=e)
        return success

    @staticmethod
    def process_revoked_shares(share_managers: List[LFShareManager]) -> bool:
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
        share_manager = share_managers[0]
        success = True
        try:
            if None in [
                share_manager.source_account_id,
                share_manager.source_account_region,
                share_manager.source_database_name,
            ]:
                raise Exception(
                    'Source account details not initialized properly. Please check if the catalog account is properly onboarded on data.all'
                )
            share_manager.initialize_clients()
            share_manager.grant_pivot_role_all_database_permissions_to_shared_database()
        except Exception as e:
            log.error(f'Failed to process revoked tables due to {e}')
            share_manager.handle_share_failure_for_all_tables(
                tables=share_manager.tables, error=e, share_item_status=ShareItemStatus.Revoke_Approved.value
            )
            return False

        for table in share_manager.tables:
            share_item = ShareObjectRepository.find_sharable_item(
                share_manager.session, share_manager.share.shareUri, table.tableUri
            )

            revoked_item_SM = ShareItemSM(ShareItemStatus.Revoke_Approved.value)
            new_state = revoked_item_SM.run_transition(ShareObjectActions.Start.value)
            revoked_item_SM.update_state_single_item(share_manager.session, share_item, new_state)

            try:
                log.info(f'Revoking access to table: {table.GlueTableName} ')
                share_manager.check_table_exists_in_source_database(share_item, table)

                log.info('Check resource link table exists')
                resource_link_table_exists = share_manager.check_resource_link_table_exists_in_target_database(table)
                other_table_shares_in_env = (
                    True
                    if ShareObjectRepository.other_approved_share_item_table_exists(
                        share_manager.session,
                        share_manager.target_environment.environmentUri,
                        share_item.itemUri,
                        share_item.shareItemUri,
                    )
                    else False
                )

                if resource_link_table_exists:
                    log.info('Revoking principal permissions from resource link table')
                    share_manager.revoke_principals_permissions_to_resource_link_table(table)
                    log.info('Revoking principal permissions from table in target')
                    share_manager.revoke_principals_permissions_to_table_in_target(table, other_table_shares_in_env)

                    if (share_manager.is_new_share and not other_table_shares_in_env) or not share_manager.is_new_share:
                        warn(
                            'share_manager.is_new_share will be deprecated in v2.6.0', DeprecationWarning, stacklevel=2
                        )
                        share_manager.grant_pivot_role_drop_permissions_to_resource_link_table(table)
                        share_manager.delete_resource_link_table_in_shared_database(table)

                if not other_table_shares_in_env:
                    share_manager.revoke_external_account_access_on_source_account(table)

                new_state = revoked_item_SM.run_transition(ShareItemActions.Success.value)
                revoked_item_SM.update_state_single_item(share_manager.session, share_item, new_state)

                ShareObjectRepository.update_share_item_health_status(
                    share_manager.session, share_item, None, None, share_item.lastVerificationTime
                )

            except Exception as e:
                new_state = revoked_item_SM.run_transition(ShareItemActions.Failure.value)
                revoked_item_SM.update_state_single_item(share_manager.session, share_item, new_state)
                success = False

                share_manager.handle_revoke_failure(table=table, error=e)

        try:
            if share_manager.tables:
                existing_shared_tables_in_share = ShareObjectRepository.check_existing_shared_items_of_type(
                    session=share_manager.session, uri=share_manager.share.shareUri, item_type=ShareableType.Table.value
                )
                log.info(f'Remaining tables shared in this share object = {existing_shared_tables_in_share}')

                if not existing_shared_tables_in_share:
                    log.info('Revoking permissions to target shared database...')
                    share_manager.revoke_principals_database_permissions_to_shared_database()

                    if not share_manager.is_new_share:
                        log.info('Deleting OLD target shared database...')
                        warn(
                            'share_manager.is_new_share will be deprecated in v2.6.0', DeprecationWarning, stacklevel=2
                        )
                        share_manager.delete_shared_database_in_target()

                existing_shares_with_shared_tables_in_environment = (
                    ShareObjectRepository.list_dataset_shares_and_datasets_with_existing_shared_items(
                        session=share_manager.session,
                        dataset_uri=share_manager.dataset.datasetUri,
                        environment_uri=share_manager.target_environment.environmentUri,
                        item_type=ShareableType.Table.value,
                    )
                )
                warn(
                    'ShareObjectRepository.list_dataset_shares_and_datasets_with_existing_shared_items will be deprecated in v2.6.0',
                    DeprecationWarning,
                    stacklevel=2,
                )
                existing_old_shares_bool = [
                    share_manager.glue_client_in_target.database_exists(item['databaseName'])
                    for item in existing_shares_with_shared_tables_in_environment
                ]
                log.info(
                    f'Remaining tables shared from this dataset to this environment = {existing_shares_with_shared_tables_in_environment}, {existing_old_shares_bool}'
                )
                if share_manager.is_new_share and False not in existing_old_shares_bool:
                    log.info('Deleting target shared database...')
                    warn('share_manager.is_new_share will be deprecated in v2.6.0', DeprecationWarning, stacklevel=2)
                    share_manager.delete_shared_database_in_target()
        except Exception as e:
            log.error(
                f'Failed to clean-up database permissions or delete shared database {share_manager.shared_db_name} '
                f'due to: {e}'
            )
            success = False
        return success

    @staticmethod
    def verify_shares(share_managers: List[LFShareManager]) -> bool:
        log.info('##### Starting Verify tables #######')
        share_manager = share_managers[0]
        if not share_manager.tables:
            log.info('No tables to verify. Skipping...')
        else:
            try:
                if None in [
                    share_manager.source_account_id,
                    share_manager.source_account_region,
                    share_manager.source_database_name,
                ]:
                    raise Exception(
                        'Source account details not initialized properly. Please check if the catalog account is properly onboarded on data.all'
                    )
                share_manager.initialize_clients()
                if not share_manager.check_pivot_role_permissions_to_source_database():
                    share_manager.grant_pivot_role_all_database_permissions_to_source_database()
                shared_database_exists = share_manager.check_shared_database_in_target()
                if shared_database_exists and not share_manager.check_pivot_role_permissions_to_shared_database():
                    share_manager.grant_pivot_role_all_database_permissions_to_shared_database()
                share_manager.check_principals_permissions_to_shared_database()
            except Exception as e:
                share_manager.db_level_errors = [str(e)]

            for table in share_manager.tables:
                try:
                    share_item = ShareObjectRepository.find_sharable_item(
                        share_manager.session, share_manager.share.shareUri, table.tableUri
                    )
                    share_manager.verify_table_exists_in_source_database(share_item, table)

                    if share_manager.cross_account:
                        share_manager.check_target_account_permissions_to_source_table(table)

                        if not RamClient.check_ram_invitation_status(
                            source_account_id=share_manager.source_account_id,
                            source_region=share_manager.source_account_region,
                            target_account_id=share_manager.target_environment.AwsAccountId,
                            source_database=share_manager.source_database_name,
                            source_table_name=table.GlueTableName,
                        ):
                            share_manager.tbl_level_errors.append(
                                ShareErrorFormatter.missing_permission_error_msg(
                                    share_manager.target_environment.AwsAccountId,
                                    'RAM Invitation',
                                    'ASSOCIATED',
                                    'Glue Table',
                                    f'{share_manager.source_database_name}.{table.GlueTableName}',
                                )
                            )

                    share_manager.verify_resource_link_table_exists_in_target_database(table)
                    share_manager.check_principals_permissions_to_table_in_target(table)
                    share_manager.check_principals_permissions_to_resource_link_table(table)

                except Exception as e:
                    share_manager.tbl_level_errors = [str(e)]

                if len(share_manager.db_level_errors) or len(share_manager.tbl_level_errors):
                    ShareObjectRepository.update_share_item_health_status(
                        share_manager.session,
                        share_item,
                        ShareItemHealthStatus.Unhealthy.value,
                        ' | '.join(share_manager.db_level_errors) + ' | ' + ' | '.join(share_manager.tbl_level_errors),
                        datetime.now(),
                    )
                else:
                    ShareObjectRepository.update_share_item_health_status(
                        share_manager.session, share_item, ShareItemHealthStatus.Healthy.value, None, datetime.now()
                    )
        return True
