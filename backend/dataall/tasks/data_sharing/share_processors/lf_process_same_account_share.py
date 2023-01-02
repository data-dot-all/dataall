import logging

from ..share_managers import LFShareManager
from ....db import models, api

log = logging.getLogger(__name__)


class ProcessLFSameAccountShare(LFShareManager):
    def __init__(
        self,
        session,
        dataset: models.Dataset,
        share: models.ShareObject,
        shared_tables: [models.DatasetTable],
        revoked_tables: [models.DatasetTable],
        source_environment: models.Environment,
        target_environment: models.Environment,
        env_group: models.EnvironmentGroup,
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
        Approves a share request for same account sharing
        1) Gets share principals
        2) Creates the shared database if doesn't exist
        3) For each share request item:
            a) update its status to share in progress
            b) check if share item exists on glue catalog raise error if not and flag share item status to failed
            e) create resource link on same account
            g) grant permission to resource link for team role on source account
            h) update share item status to share successful
        4) Update shareddb by removing items not part of the share request
        5) Delete deprecated shareddb

        Returns
        -------
        True if share is successful
        """
        log.info(
            '##### Starting Sharing tables same account #######'
        )

        self.grant_pivot_role_all_database_permissions()

        shared_db_name = self.build_shared_db_name()
        principals = self.get_share_principals()

        self.create_shared_database(
            self.target_environment, self.dataset, shared_db_name, principals
        )

        for table in self.shared_tables:

            share_item = api.ShareObject.find_share_item_by_table(
                self.session, self.share, table
            )

            if not share_item:
                log.info(
                    f'Share Item not found for {self.share.shareUri} '
                    f'and Dataset Table {table.GlueTableName} continuing loop...'
                )
                continue
            shared_item_SM = api.ShareItemSM(models.ShareItemStatus.Share_Approved.value)
            new_state = shared_item_SM.run_transition(models.Enums.ShareObjectActions.Start.value)
            shared_item_SM.update_state_single_item(self.session, share_item, new_state)

            try:
                log.info(f'Starting sharing access for table: {table.GlueTableName}')
                self.check_share_item_exists_on_glue_catalog(share_item, table)

                data = self.build_share_data(principals, table)
                self.create_resource_link(**data)

                new_state = shared_item_SM.run_transition(models.Enums.ShareItemActions.Success.value)
                shared_item_SM.update_state_single_item(self.session, share_item, new_state)

            except Exception as e:
                self.handle_share_failure(table, share_item, e)
                new_state = shared_item_SM.run_transition(models.Enums.ShareItemActions.Failure.value)
                shared_item_SM.update_state_single_item(self.session, share_item, new_state)

        return True

    def process_revoked_shares(self) -> bool:
        """
        Loops through share request items and revokes access on LF
        Returns
        -------
        True if revoke is successful
        """

        for table in self.revoked_tables:
            share_item = api.ShareObject.find_share_item_by_table(
                self.session, self.share, table
            )
            if not share_item:
                log.info(
                    f'Share Item not found for {self.share.shareUri} '
                    f'and Dataset Table {table.GlueTableName} continuing loop...'
                )
                continue

            revoked_item_SM = api.ShareItemSM(models.ShareItemStatus.Revoke_Approved.value)
            new_state = revoked_item_SM.run_transition(models.Enums.ShareObjectActions.Start.value)
            revoked_item_SM.update_state_single_item(self.session, share_item, new_state)

            try:
                self.check_share_item_exists_on_glue_catalog(share_item, table)

                log.info(f'Starting revoke access for table: {table.GlueTableName}')

                self.revoke_table_resource_link_access(table)

                self.revoke_source_table_access(table)

                self.delete_resource_link_table(table)

                new_state = revoked_item_SM.run_transition(models.Enums.ShareItemActions.Success.value)
                revoked_item_SM.update_state_single_item(self.session, share_item, new_state)

            except Exception as e:
                self.handle_revoke_failure(share_item, table, e)
                new_state = revoked_item_SM.run_transition(models.Enums.ShareItemActions.Failure.value)
                revoked_item_SM.update_state_single_item(self.session, share_item, new_state)

        return True

    def clean_up_share(self) -> bool:
        """
        Deletes shared database when share request is rejected

        Returns
        -------
        bool
        """
        self.delete_shared_database()
        return True
