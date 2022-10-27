import abc
import logging
import uuid

from ....aws.handlers.glue import Glue
from ....aws.handlers.lakeformation import LakeFormation
from ....aws.handlers.sts import SessionHelper
from ....db import models, api, exceptions
from ....utils.alarm_service import AlarmService

log = logging.getLogger(__name__)


class LFShareRevoke:
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
        self.session = session
        self.env_group = env_group
        self.dataset = dataset
        self.share = share
        self.shared_tables = shared_tables
        self.source_environment = source_environment
        self.target_environment = target_environment
        self.shared_db_name = shared_db_name

    @abc.abstractmethod
    def revoke_share(self):
        return NotImplementedError

    def revoke_shared_tables_access(self) -> bool:
        """
        Loops through share request items and revokes access on LF
        Returns
        -------
        True if revoke is successful
        """

        for table in self.shared_tables:
            share_item = api.ShareObject.find_share_item_by_table(
                self.session, self.share, table
            )

            api.ShareObject.update_share_item_status(
                self.session,
                share_item,
                models.ShareObjectStatus.Revoke_In_Progress.value,
            )

            try:

                log.info(f'Starting revoke access for table: {table.GlueTableName}')

                self.revoke_table_resource_link_access(table)

                self.revoke_source_table_access(table)

                api.ShareObject.update_share_item_status(
                    self.session,
                    share_item,
                    models.ShareObjectStatus.Revoke_Share_Succeeded.value,
                )

            except Exception as e:
                self.handle_revoke_failure(share_item, table, e)

        return True

    def revoke_table_resource_link_access(self, table: models.DatasetTable):
        """
        Revokes access to glue table resource link
        Parameters
        ----------
        table : models.DatasetTable

        Returns
        -------
        True if revoke is successful
        """
        if not Glue.table_exists(
            accountid=self.target_environment.AwsAccountId,
            region=self.target_environment.region,
            database=self.shared_db_name,
            tablename=table.GlueTableName,
        ):
            log.info(
                f'Resource link could not be found '
                f'on {self.target_environment.AwsAccountId}/{self.shared_db_name}/{table.GlueTableName} '
                f'skipping revoke actions...'
            )
            return True

        log.info(
            f'Revoking resource link access '
            f'on {self.target_environment.AwsAccountId}/{self.shared_db_name}/{table.GlueTableName} '
            f'for principal {self.env_group.environmentIAMRoleArn}'
        )
        LakeFormation.batch_revoke_permissions(
            SessionHelper.remote_session(self.target_environment.AwsAccountId).client(
                'lakeformation', region_name=self.target_environment.region
            ),
            self.target_environment.AwsAccountId,
            [
                {
                    'Id': str(uuid.uuid4()),
                    'Principal': {
                        'DataLakePrincipalIdentifier': self.env_group.environmentIAMRoleArn
                    },
                    'Resource': {
                        'Table': {
                            'DatabaseName': self.shared_db_name,
                            'Name': table.GlueTableName,
                            'CatalogId': self.target_environment.AwsAccountId,
                        }
                    },
                    'Permissions': ['DESCRIBE'],
                }
            ],
        )
        return True

    def revoke_source_table_access(self, table):
        """
        Revokes access to the source glue table
        Parameters
        ----------
        table : models.DatasetTable

        Returns
        -------
        True if revoke is successful
        """
        if not Glue.table_exists(
            accountid=self.target_environment.AwsAccountId,
            region=self.target_environment.region,
            database=self.shared_db_name,
            tablename=table.GlueTableName,
        ):
            log.info(
                f'Source table could not be found '
                f'on {self.source_environment.AwsAccountId}/{self.dataset.GlueDatabaseName}/{table.GlueTableName} '
                f'skipping revoke actions...'
            )
            return True

        log.info(
            f'Revoking source table access '
            f'on {self.source_environment.AwsAccountId}/{self.dataset.GlueDatabaseName}/{table.GlueTableName} '
            f'for principal {self.env_group.environmentIAMRoleArn}'
        )
        LakeFormation.revoke_source_table_access(
            target_accountid=self.target_environment.AwsAccountId,
            region=self.target_environment.region,
            source_database=self.dataset.GlueDatabaseName,
            source_table=table.GlueTableName,
            target_principal=self.env_group.environmentIAMRoleArn,
            source_accountid=self.source_environment.AwsAccountId,
        )
        return True

    def delete_shared_database(self) -> bool:
        """
        Deletes shared database when share request is rejected

        Returns
        -------
        bool
        """
        log.info(f'Deleting shared database {self.shared_db_name}')
        return Glue.delete_database(
            accountid=self.target_environment.AwsAccountId,
            region=self.target_environment.region,
            database=self.shared_db_name,
        )

    def check_share_item_exists_on_glue_catalog(
        self, share_item: models.ShareObjectItem, table: models.DatasetTable
    ) -> None:
        """
        Checks if a table in the share request
        still exists on the Glue catalog before revoking share

        Parameters
        ----------
        share_item : request share item
        table : dataset table

        Returns
        -------
        exceptions.AWSResourceNotFound
        """
        if not Glue.table_exists(
            accountid=self.source_environment.AwsAccountId,
            region=self.source_environment.region,
            database=table.GlueDatabaseName,
            tablename=table.GlueTableName,
        ):
            raise exceptions.AWSResourceNotFound(
                action='RevokeShare',
                message=(
                    f'Share Item {share_item.itemUri} found on share request'
                    f' but its correspondent Glue table {table.GlueTableName} does not exist.'
                ),
            )

    def handle_revoke_failure(
        self,
        table: models.DatasetTable,
        share_item: models.ShareObjectItem,
        error: Exception,
    ) -> bool:
        """
        Handles revoke failure by raising an alarm to alarmsTopic
        Parameters
        ----------
        table : dataset table
        share_item : failed item
        error : share error

        Returns
        -------
        True if alarm published successfully
        """
        logging.error(
            f'Failed to revoke LF permissions to  table share {table.GlueTableName} '
            f'on target account {self.target_environment.AwsAccountId}/{self.target_environment.region}'
            f'due to: {error}'
        )
        api.ShareObject.update_share_item_status(
            self.session,
            share_item,
            models.ShareObjectStatus.Revoke_Share_Failed.value,
        )
        AlarmService().trigger_revoke_sharing_failure_alarm(
            table, self.share, self.target_environment
        )
        return True
