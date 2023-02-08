import logging


from ..share_managers import LFShareManager
from ....aws.handlers.ram import Ram
from ....db import models, api

log = logging.getLogger(__name__)


class ProcessLFCrossAccountShare(LFShareManager):
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
            '##### Starting Sharing tables cross account #######'
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
                log.info(f"Sharing table {table.GlueTableName}...")

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

                    self.check_share_item_exists_on_glue_catalog(share_item, table)

                    data = self.build_share_data(table)
                    self.share_table_with_target_account(**data)

                    (
                        retry_share_table,
                        failed_invitations,
                    ) = Ram.accept_ram_invitation(**data)

                    if retry_share_table:
                        self.share_table_with_target_account(**data)
                        Ram.accept_ram_invitation(**data)

                    self.create_resource_link(**data)

                    new_state = shared_item_SM.run_transition(models.Enums.ShareItemActions.Success.value)
                    shared_item_SM.update_state_single_item(self.session, share_item, new_state)

                except Exception as e:
                    self.handle_share_failure(table=table, share_item=share_item, error=e)
                    new_state = shared_item_SM.run_transition(models.Enums.ShareItemActions.Failure.value)
                    shared_item_SM.update_state_single_item(self.session, share_item, new_state)
                    success = False

        return success

    def process_revoked_shares(self) -> bool:
        """
        For each revoked request item:
            a) update its status to REVOKE_IN_PROGRESS with Action Start
            b) check if item exists on glue catalog raise error if not and flag item status to failed
            c) revoke table resource link: undo grant permission to resource link table for team role in target account
            d) revoke source table access: undo grant permission to table for team role in source account
            e) delete resource link table
            h) update share item status to REVOKE_SUCCESSFUL with Action Success

        Returns
        -------
        True if share is revoked successfully
        False if revoke fails
        """
        log.info(
            '##### Starting Revoking tables cross account #######'
        )
        success = True
        shared_db_name = self.build_shared_db_name()
        principals = self.get_share_principals()
        for table in self.revoked_tables:
            share_item = api.ShareObject.find_share_item_by_table(
                self.session, self.share, table
            )

            revoked_item_SM = api.ShareItemSM(models.ShareItemStatus.Revoke_Approved.value)
            new_state = revoked_item_SM.run_transition(models.Enums.ShareObjectActions.Start.value)
            revoked_item_SM.update_state_single_item(self.session, share_item, new_state)

            try:

                self.check_share_item_exists_on_glue_catalog(share_item, table)

                log.info(f'Starting revoke access for table: {table.GlueTableName} in database {shared_db_name} '
                         f'For principals {principals}')

                self.revoke_table_resource_link_access(table, principals)

                self.revoke_source_table_access(table, principals)

                self.delete_resource_link_table(table)

                new_state = revoked_item_SM.run_transition(models.Enums.ShareItemActions.Success.value)
                revoked_item_SM.update_state_single_item(self.session, share_item, new_state)

            except Exception as e:
                self.handle_revoke_failure(share_item=share_item, table=table, error=e)
                new_state = revoked_item_SM.run_transition(models.Enums.ShareItemActions.Failure.value)
                revoked_item_SM.update_state_single_item(self.session, share_item, new_state)
                success = False

        return success

    def clean_up_share(self) -> bool:
        """"
        1) deletes deprecated shared db in target account
        2) checks if there are other share objects from this source account to this target account.
        If not, it revokes external account access of the target account to the source account.
        Returns
        -------
        True if clean-up succeeds
        """

        self.delete_shared_database()

        if not api.ShareObject.other_approved_share_object_exists(
                self.session,
                self.target_environment.environmentUri,
                self.dataset.datasetUri,
        ):
            self.revoke_external_account_access_on_source_account()

        return True
