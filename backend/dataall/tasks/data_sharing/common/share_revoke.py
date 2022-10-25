import abc
import logging
import uuid

from ....aws.handlers.glue import Glue
from ....aws.handlers.lakeformation import LakeFormation
from ....aws.handlers.sts import SessionHelper
from ....db import models, api, exceptions
from ....utils.alarm_service import AlarmService

log = logging.getLogger(__name__)


class ShareRevoke:
    def __init__(
        self,
        session,
        shared_db_name,
        env_group,
        dataset,
        share,
        shared_tables,
        source_environment,
        target_environment,
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

    def revoke_resource_links_access(self) -> [dict]:
        """
        Loops through share request items and revokes access on LF
        Returns
        -------
        List of revoke entries
        """
        aws_session = SessionHelper.remote_session(
            accountid=self.target_environment.AwsAccountId
        )
        client = aws_session.client(
            'lakeformation', region_name=self.target_environment.region
        )
        revoke_entries = []

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
                data = {
                    'accountid': self.target_environment.AwsAccountId,
                    'region': self.target_environment.region,
                    'database': self.shared_db_name,
                    'tablename': table.GlueTableName,
                }

                log.info(f'Starting revoke for: {data}')

                if Glue.table_exists(**data):
                    revoke_entries.append(
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
                            'Permissions': ['DESCRIBE', 'SELECT'],
                        }
                    )

                    log.info(f'Revoking permissions for entries : {revoke_entries}')

                    LakeFormation.batch_revoke_permissions(
                        client, self.target_environment.AwsAccountId, revoke_entries
                    )

                api.ShareObject.update_share_item_status(
                    self.session,
                    share_item,
                    models.ShareObjectStatus.Revoke_Share_Succeeded.value,
                )

            except Exception as e:
                logging.error(
                    f'Failed to revoke LF permissions to  table share {table.GlueTableName} '
                    f'on target account {self.target_environment.AwsAccountId}/{self.target_environment.region}'
                    f'due to: {e}'
                )
                api.ShareObject.update_share_item_status(
                    self.session,
                    share_item,
                    models.ShareObjectStatus.Revoke_Share_Failed.value,
                )
                AlarmService().trigger_revoke_sharing_failure_alarm(
                    table, self.share, self.target_environment
                )

        return revoke_entries

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
