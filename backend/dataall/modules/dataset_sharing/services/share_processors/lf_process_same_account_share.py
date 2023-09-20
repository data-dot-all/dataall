import logging

from dataall.core.environment.db.environment_models import Environment, EnvironmentGroup
from dataall.modules.dataset_sharing.db.enums import ShareItemStatus, ShareObjectActions, ShareItemActions
from dataall.modules.dataset_sharing.db.share_object_models import ShareObject
from dataall.modules.dataset_sharing.db.share_object_repositories import ShareObjectRepository, ShareItemSM
from ..share_managers import LFShareManager
from dataall.modules.datasets_base.db.dataset_models import DatasetTable, Dataset

log = logging.getLogger(__name__)


class ProcessLFSameAccountShare(LFShareManager):
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
            c) create resource link in account
            d) grant permission to table for requester team IAM role in account
            e) grant permission to resource link table for requester team IAM role in account
            f) update share item status to SHARE_SUCCESSFUL with Action Success

        Returns
        -------
        True if share is granted successfully
        """
        log.info(
            '##### Starting Sharing tables same account #######'
        )

        success = True
        if not self.shared_tables:
            log.info("No tables to share. Skipping...")

        else:
            self.grant_pivot_role_all_database_permissions()

            shared_db_name = self.build_shared_db_name()
            principals = self.get_share_principals()

            self.create_shared_database(
                self.target_environment, self.dataset, shared_db_name, principals
            )

        for table in self.shared_tables:

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
                log.info(f'Starting sharing access for table: {table.GlueTableName}')
                self.check_share_item_exists_on_glue_catalog(share_item, table)

                data = self.build_share_data(table)
                self.create_resource_link(**data)

                new_state = shared_item_SM.run_transition(ShareItemActions.Success.value)
                shared_item_SM.update_state_single_item(self.session, share_item, new_state)

            except Exception as e:
                self.handle_share_failure(table, share_item, e)
                new_state = shared_item_SM.run_transition(ShareItemActions.Failure.value)
                shared_item_SM.update_state_single_item(self.session, share_item, new_state)
                success = False

        return success

    def process_revoked_shares(self) -> bool:
        """
        For each revoked request item:
            a) update its status to REVOKE_IN_PROGRESS with Action Start
            b) check if item exists on glue catalog raise error if not and flag item status to failed
            c) revoke table resource link: undo grant permission to resource link table for team role in account
            d) revoke source table access: undo grant permission to table for team role in account
            e) delete resource link table
            h) update share item status to REVOKE_SUCCESSFUL with Action Success

        Returns
        -------
        True if share is revoked successfully
        False if revoke fails
        """
        success = True
        shared_db_name = self.build_shared_db_name()
        principals = self.get_share_principals()
        for table in self.revoked_tables:
            share_item = ShareObjectRepository.find_sharable_item(
                self.session, self.share.shareUri, table.tableUri
            )
            if not share_item:
                log.info(
                    f'Share Item not found for {self.share.shareUri} '
                    f'and Dataset Table {table.GlueTableName} continuing loop...'
                )
                continue

            revoked_item_SM = ShareItemSM(ShareItemStatus.Revoke_Approved.value)
            new_state = revoked_item_SM.run_transition(ShareObjectActions.Start.value)
            revoked_item_SM.update_state_single_item(self.session, share_item, new_state)

            try:
                self.check_share_item_exists_on_glue_catalog(share_item, table)

                log.info(f'Starting revoke access for table: {table.GlueTableName} in database {shared_db_name} '
                         f'For principals {principals}')

                self.revoke_table_resource_link_access(table, principals)

                principals = [p for p in principals if "arn:aws:quicksight" not in p]

                self.revoke_source_table_access(table, principals)

                self.delete_resource_link_table(table)

                new_state = revoked_item_SM.run_transition(ShareItemActions.Success.value)
                revoked_item_SM.update_state_single_item(self.session, share_item, new_state)

            except Exception as e:
                self.handle_revoke_failure(share_item, table, e)
                new_state = revoked_item_SM.run_transition(ShareItemActions.Failure.value)
                revoked_item_SM.update_state_single_item(self.session, share_item, new_state)
                success = False

        return success

    def clean_up_share(self) -> bool:
        """"
        1) deletes deprecated shared db in target account
        Returns
        -------
        True if clean-up succeeds
        """
        self.delete_shared_database()
        return True
