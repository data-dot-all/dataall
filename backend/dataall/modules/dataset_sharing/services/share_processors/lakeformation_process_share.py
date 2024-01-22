import logging

from dataall.core.environment.db.environment_models import Environment, EnvironmentGroup
from dataall.modules.dataset_sharing.db.enums import ShareItemStatus, ShareObjectActions, ShareItemActions, ShareableType
from ..share_managers import LFShareManager
from dataall.modules.dataset_sharing.aws.ram_client import RamClient
from dataall.modules.datasets_base.db.dataset_models import DatasetTable, Dataset
from dataall.modules.dataset_sharing.db.share_object_models import ShareObject
from dataall.modules.dataset_sharing.db.share_object_repositories import ShareObjectRepository, ShareItemSM

log = logging.getLogger(__name__)


class ProcessLakeFormationShare(LFShareManager):
    def __init__(
        self,
        session,
        dataset: Dataset,
        share: ShareObject,
        shared_tables: [DatasetTable],
        revoked_tables: [DatasetTable],
        source_environment: Environment,
        target_environment: Environment,
        env_group: EnvironmentGroup,
    ):
        super().__init__(
            session,
            dataset,
            share,
            shared_tables,
            revoked_tables,
            source_environment,
            target_environment,
            env_group,
        )

    def process_approved_shares(self) -> bool:
        """
        1) Grant ALL permissions to pivotRole for source database in source account
        2) Get share principals (requester IAM role and QS groups) and build shared db name
        3) Create the shared database in target account if it doesn't exist
        4) For each shared table:
            a) update its status to SHARE_IN_PROGRESS with Action Start
            b) check if share item exists on glue catalog raise error if not and flag share item status to failed
            c) grant external account (target account) access to table -> create RAM invitation and revoke_iamallowedgroups_super_permission_from_table
            d) accept pending RAM invitation
            e) create resource link for table in target account
            f) grant permission to table for requester team IAM role in source account
            g) grant permission to resource link table for requester team IAM role in target account
            h) update share item status to SHARE_SUCCESSFUL with Action Success

        Returns
        -------
        True if share is granted successfully
        False if share fails
        """

        log.info(
            '##### Starting Sharing tables #######'
        )
        success = True
        if not self.shared_tables:
            log.info("No tables to share. Skipping...")
        else:
            self.grant_pivot_role_all_database_permissions_to_source_database()
            self.check_if_exists_and_create_shared_database_in_target()
            self.grant_pivot_role_all_database_permissions_to_shared_database()
            self.grant_principals_database_permissions_to_shared_database()

            for table in self.shared_tables:
                log.info(f"Sharing table {table.GlueTableName}...")

                share_item = ShareObjectRepository.find_sharable_item(
                    self.session, self.share.shareUri, table.tableUri
                )

                if not share_item:
                    log.info(
                        f'Share Item not found for {self.share.shareUri} '
                        f'and Dataset Table {table.GlueTableName} continuing loop...'
                    )
                    continue

                shared_item_SM = ShareItemSM(ShareItemStatus.Share_Approved.value)
                new_state = shared_item_SM.run_transition(ShareObjectActions.Start.value)
                shared_item_SM.update_state_single_item(self.session, share_item, new_state)

                try:
                    self.check_table_exists_in_source_database(share_item, table)

                    if self.cross_account:
                        log.info('Processing cross-account permissions...')
                        # TODO: old shares, add if exists, use LFV3
                        self.share_table_with_target_account(table)
                        (
                            retry_share_table,
                            failed_invitations,
                        ) = RamClient.accept_ram_invitation(
                            source_account_id=self.source_environment.AwsAccountId,
                            source_region=self.source_environment.region,
                            target_account_id=self.target_environment.AwsAccountId,
                            target_region=self.target_environment.region,
                            source_database=self.dataset.GlueDatabaseName,
                            source_table=table
                        )

                        if retry_share_table:
                            self.share_table_with_target_account(table)
                            RamClient.accept_ram_invitation(
                                source_account_id=self.source_environment.AwsAccountId,
                                source_region=self.source_environment.region,
                                target_account_id=self.target_environment.AwsAccountId,
                                target_region=self.target_environment.region,
                                source_database=self.dataset.GlueDatabaseName,
                                source_table=table
                            )
                    self.grant_principals_permissions_to_table_in_target(table) #TODO WITH LFV3 we might be able to remove this
                    self.check_if_exists_and_create_resource_link_table_in_shared_database(table)
                    self.grant_principals_permissions_to_resource_link_table(table)

                    new_state = shared_item_SM.run_transition(ShareItemActions.Success.value)
                    shared_item_SM.update_state_single_item(self.session, share_item, new_state)

                except Exception as e:
                    # must run first to ensure state transitions to failed
                    new_state = shared_item_SM.run_transition(ShareItemActions.Failure.value)
                    shared_item_SM.update_state_single_item(self.session, share_item, new_state)
                    success = False

                    # statements which can throw exceptions but are not critical
                    self.handle_share_failure(table=table, error=e)

        return success

    def process_revoked_shares(self) -> bool:
        """
        For each revoked request item:
            a) update its status to REVOKE_IN_PROGRESS with Action Start
            b) check if item exists on glue catalog raise error if not and flag item status to failed
            c) revoke table resource link: undo grant permission to resource link table for team role in target account
            d) revoke source table access: undo grant permission to table for team role in source account (and for QS Group if no other shares present for table)
            e) delete resource link table
            h) update share item status to REVOKE_SUCCESSFUL with Action Success

        Returns
        -------
        True if share is revoked successfully
        False if revoke fails
        """
        log.info(
            '##### Starting Revoking tables #######'
        )
        success = True
        shared_db_name = self.build_shared_db_name()
        principals = self.get_share_principals()
        for table in self.revoked_tables:
            share_item = ShareObjectRepository.find_sharable_item(
                self.session, self.share.shareUri, table.tableUri
            )

            revoked_item_SM = ShareItemSM(ShareItemStatus.Revoke_Approved.value)
            new_state = revoked_item_SM.run_transition(ShareObjectActions.Start.value)
            revoked_item_SM.update_state_single_item(self.session, share_item, new_state)

            try:
                log.info(f'Starting revoke access for table: {table.GlueTableName} in database {shared_db_name} '
                         f'For principals {principals}')

                self.check_table_exists_in_source_database(share_item, table)
                existing = self.check_resource_link_table_exists_in_target_database(table)
                if existing:
                    self.revoke_principals_permissions_to_resource_link_table(table)
                    self.revoke_principals_permissions_to_table_in_target(table)

                other_table_shares_in_env = True if ShareObjectRepository.other_approved_share_item_table_exists(
                    self.session,
                    self.target_environment.environmentUri,
                    share_item.itemUri,
                    share_item.shareItemUri
                ) else False

                if not other_table_shares_in_env:
                    self.revoke_external_account_access_on_source_account(table)

                if (self.is_new_share and not other_table_shares_in_env) or not self.is_new_share:
                    self.delete_resource_link_table_in_shared_database(table)

                new_state = revoked_item_SM.run_transition(ShareItemActions.Success.value)
                revoked_item_SM.update_state_single_item(self.session, share_item, new_state)

            except Exception as e:
                # must run first to ensure state transitions to failed
                new_state = revoked_item_SM.run_transition(ShareItemActions.Failure.value)
                revoked_item_SM.update_state_single_item(self.session, share_item, new_state)
                success = False

                # statements which can throw exceptions but are not critical
                self.handle_revoke_failure(table=table, error=e)

        try:
            # TODO: logic to check all shares with table shares in environment
            existing_shared_items = ShareObjectRepository.check_existing_shared_items_of_type(
                self.session,
                self.share.shareUri,
                ShareableType.Table.value
            )
            log.info(f'Still remaining LF resources shared = {existing_shared_items}')
            if not existing_shared_items and self.revoked_tables:
                log.info("Clean up LF remaining resources...")
                clean_up_tables = self.delete_shared_database_in_target()
                log.info(f"Clean up LF successful = {clean_up_tables}")
        except Exception as e:
            success = False

        return success
