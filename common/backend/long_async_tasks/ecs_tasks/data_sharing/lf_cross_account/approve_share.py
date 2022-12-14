import logging
import time

from botocore.exceptions import ClientError

from ..common.lf_share_approval import LFShareApproval
from ....aws.handlers.lakeformation import LakeFormation
from ....aws.handlers.ram import Ram
from ....aws.handlers.sts import SessionHelper
from ....db import models, api

log = logging.getLogger(__name__)


class CrossAccountShareApproval(LFShareApproval):
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

    def approve_share(
        self,
    ) -> bool:
        """
        1) Gets share principals
        2) Creates the shared database if doesn't exist
        3) For each share request item:
            a) update its status to share in progress
            b) check if share item exists on glue catalog raise error if not and flag share item status to failed
            c) grant external account to target account
            d) accept Ram invitation if pending
            e) create resource link on target account
            f) grant permission to resource link for team role on target account
            g) grant permission to resource link for team role on source account
            h) update share item status to share successful
         4) Update shareddb by removing items not part of the share request
         5) Delete deprecated shareddb

        Returns
        -------
        True if share is approved successfully
        """
        log.info(
            '##### Starting Sharing tables cross account #######'
        )
        principals = self.get_share_principals()

        self.create_shared_database(
            self.target_environment, self.dataset, self.shared_db_name, principals
        )

        for table in self.shared_tables:

            share_item = api.ShareObject.find_share_item_by_table(
                self.session, self.share, table
            )

            api.ShareObject.update_share_item_status(
                self.session,
                share_item,
                models.ShareObjectStatus.Share_In_Progress.value,
            )

            try:

                self.check_share_item_exists_on_glue_catalog(share_item, table)

                data = self.build_share_data(principals, table)

                self.share_table_with_target_account(**data)

                (
                    retry_share_table,
                    failed_invitations,
                ) = Ram.accept_ram_invitation(**data)

                if retry_share_table:
                    self.share_table_with_target_account(**data)
                    Ram.accept_ram_invitation(**data)

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

    @classmethod
    def share_table_with_target_account(cls, **data):
        """
        Shares tables using Lake Formation
        Sharing feature may take some extra seconds
        :param data:
        :return:
        """
        source_accountid = data['source']['accountid']
        source_region = data['source']['region']

        target_accountid = data['target']['accountid']
        target_region = data['target']['region']

        source_session = SessionHelper.remote_session(accountid=source_accountid)
        source_lf_client = source_session.client(
            'lakeformation', region_name=source_region
        )
        try:

            LakeFormation.revoke_iamallowedgroups_super_permission_from_table(
                source_lf_client,
                source_accountid,
                data['source']['database'],
                data['source']['tablename'],
            )
            time.sleep(1)

            LakeFormation.grant_permissions_to_table(
                source_lf_client,
                target_accountid,
                data['source']['database'],
                data['source']['tablename'],
                ['DESCRIBE', 'SELECT'],
                ['DESCRIBE', 'SELECT'],
            )
            time.sleep(2)

            log.info(
                f"Granted access to table {data['source']['tablename']} "
                f'to external account {target_accountid} '
            )
            return True

        except ClientError as e:
            logging.error(
                f'Failed granting access to table {data["source"]["tablename"]} '
                f'from {source_accountid} / {source_region} '
                f'to external account{target_accountid}/{target_region}'
                f'due to: {e}'
            )
            raise e
