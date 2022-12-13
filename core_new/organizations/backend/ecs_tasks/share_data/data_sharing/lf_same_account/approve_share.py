import logging

from ..common.lf_share_approval import LFShareApproval
from ....db import models, api

log = logging.getLogger(__name__)


class SameAccountShareApproval(LFShareApproval):
    def __init__(
        self,
        session,
        shared_db_name: str,
        dataset: models.Dataset,
        share: models.ShareObject,
        shared_tables: [models.DatasetTable],
        source_environment: models.Environment,
        target_environment: models.Environment,
        env_group: models.EnvironmentGroup,
    ):
        super().__init__(
            session,
            shared_db_name,
            dataset,
            share,
            shared_tables,
            source_environment,
            target_environment,
            env_group,
        )

    def approve_share(self) -> bool:
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

        principals = self.get_share_principals()

        self.create_shared_database(
            self.target_environment, self.dataset, self.shared_db_name, principals
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

            api.ShareObject.update_share_item_status(
                self.session,
                share_item,
                models.ShareObjectStatus.Share_In_Progress.value,
            )

            try:

                self.check_share_item_exists_on_glue_catalog(share_item, table)

                data = self.build_share_data(principals, table)

                self.create_resource_link(**data)

                api.ShareObject.update_share_item_status(
                    self.session,
                    share_item,
                    models.ShareObjectStatus.Share_Succeeded.value,
                )

            except Exception as e:
                self.handle_share_failure(table, share_item, e)

        self.clean_shared_database()

        self.delete_deprecated_shared_database()

        return True
