import logging
import time

from botocore.exceptions import ClientError

from ..common.lf_share_manager import LFShareManager
from ....aws.handlers.lakeformation import LakeFormation
from ....aws.handlers.ram import Ram
from ....aws.handlers.sts import SessionHelper
from ....db import models, api

log = logging.getLogger(__name__)


class CrossAccountShareApproval(LFShareManager):
    def __init__(
        self,
        session,
        shared_db_name: str,
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
            shared_db_name,
            dataset,
            share,
            shared_tables,
            revoked_tables,
            source_environment,
            target_environment,
            env_group,
        )

    def process_share(
        self,
        shared_item_SM: api.ShareItemSM,
        revoked_item_SM: api.ShareItemSM
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

            new_state = shared_item_SM.run_transition(models.Enums.ShareObjectActions.Start.value)
            shared_item_SM.update_state_single_item(self.session, share_item, new_state)

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

                new_state = shared_item_SM.run_transition(models.Enums.ShareItemActions.Success.value)
                shared_item_SM.update_state_single_item(self.session, share_item, new_state)

            except Exception as e:
                self.handle_share_failure(table, share_item, e)
                new_state = shared_item_SM.run_transition(models.Enums.ShareItemActions.Failure.value)
                shared_item_SM.update_state_single_item(self.session, share_item, new_state)

        for table in self.revoked_tables:
            share_item = api.ShareObject.find_share_item_by_table(
                self.session, self.share, table
            )
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

        self.delete_shared_database()

        if not api.ShareObject.other_approved_share_object_exists(
                self.session,
                self.target_environment.environmentUri,
                self.dataset.datasetUri,
        ):
            self.revoke_external_account_access_on_source_account()

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

    @classmethod
    def revoke_external_account_access_on_source_account(self) -> [dict]:
        """
        1) Revokes access to external account
        if dataset is not shared with any other team from the same workspace
        2) Deletes resource_shares on RAM associated to revoked tables

        Returns
        -------
        List of revoke entries
        """
        log.info(
            f'Revoking Access for AWS account: {self.target_environment.AwsAccountId}'
        )
        aws_session = SessionHelper.remote_session(
            accountid=self.source_environment.AwsAccountId
        )
        client = aws_session.client(
            'lakeformation', region_name=self.source_environment.region
        )
        revoke_entries = []
        for table in self.revoked_tables:
            revoke_entries.append(
                {
                    'Id': str(uuid.uuid4()),
                    'Principal': {
                        'DataLakePrincipalIdentifier': self.target_environment.AwsAccountId
                    },
                    'Resource': {
                        'TableWithColumns': {
                            'DatabaseName': table.GlueDatabaseName,
                            'Name': table.GlueTableName,
                            'ColumnWildcard': {},
                            'CatalogId': self.source_environment.AwsAccountId,
                        }
                    },
                    'Permissions': ['DESCRIBE', 'SELECT'],
                    'PermissionsWithGrantOption': ['DESCRIBE', 'SELECT'],
                }
            )
            LakeFormation.batch_revoke_permissions(
                client, self.source_environment.AwsAccountId, revoke_entries
            )
        return revoke_entries

    @classmethod
    def delete_ram_resource_shares(self, resource_arn: str) -> [dict]:
        """
        Deletes resource share for the resource arn
        Parameters
        ----------
        resource_arn : glue table arn

        Returns
        -------
        list of ram associations
        """
        log.info(f'Cleaning RAM resource shares for resource: {resource_arn} ...')
        return Ram.delete_resource_shares(
            SessionHelper.remote_session(
                accountid=self.source_environment.AwsAccountId
            ).client('ram', region_name=self.source_environment.region),
            resource_arn,
        )

