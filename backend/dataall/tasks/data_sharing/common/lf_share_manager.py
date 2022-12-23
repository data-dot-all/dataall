import abc
import logging
import uuid

from botocore.exceptions import ClientError

from ....aws.handlers.glue import Glue
from ....aws.handlers.lakeformation import LakeFormation
from ....aws.handlers.quicksight import Quicksight
from ....aws.handlers.sts import SessionHelper
from ....db import api, exceptions, models
from ....utils.alarm_service import AlarmService

logger = logging.getLogger(__name__)


class LFShareManager:
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
        self.session = session
        self.env_group = env_group
        self.dataset = dataset
        self.share = share
        self.shared_tables = shared_tables
        self.revoked_tables = revoked_tables
        self.source_environment = source_environment
        self.target_environment = target_environment
        self.shared_db_name = shared_db_name

    @abc.abstractmethod
    def process_share(self, Shared_Item_SM: api.ShareItemSM, Revoked_Item_SM: api.ShareItemSM) -> [str]:
        return NotImplementedError

    @abc.abstractmethod
    def clean_up_share(self):
        return NotImplementedError

    def get_share_principals(self) -> [str]:
        """
        Builds list of principals of the share request
        Returns
        -------
        List of principals
        """
        principals = [f"arn:aws:iam::{self.target_environment.AwsAccountId}:role/{self.share.principalIAMRoleName}"]
        if self.target_environment.dashboardsEnabled:
            q_group = Quicksight.get_quicksight_group_arn(
                self.target_environment.AwsAccountId
            )
            if q_group:
                principals.append(q_group)
        return principals

    def build_share_data(self, principals: [str], table: models.DatasetTable) -> dict:
        """
        Build aws dict for boto3 operations on Glue and LF from share data
        Parameters
        ----------
        principals : team role
        table : dataset table

        Returns
        -------
        dict for boto3 operations
        """
        data = {
            'source': {
                'accountid': self.source_environment.AwsAccountId,
                'region': self.source_environment.region,
                'database': table.GlueDatabaseName,
                'tablename': table.GlueTableName,
            },
            'target': {
                'accountid': self.target_environment.AwsAccountId,
                'region': self.target_environment.region,
                'principals': principals,
                'database': self.shared_db_name,
            },
        }
        return data

    def check_share_item_exists_on_glue_catalog(
        self, share_item: models.ShareObjectItem, table: models.DatasetTable
    ) -> None:
        """
        Checks if a table in the share request
        still exists on the Glue catalog before sharing

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
                action='ProcessShare',
                message=(
                    f'Share Item {share_item.itemUri} found on share request'
                    f' but its correspondent Glue table {table.GlueTableName} does not exist.'
                ),
            )

    @classmethod
    def create_shared_database(
        cls,
        target_environment: models.Environment,
        dataset: models.Dataset,
        shared_db_name: str,
        principals: [str],
    ) -> dict:

        """
        Creates the shared database if does not exists.
        1) Grants pivot role ALL permission on shareddb
        2) Grant Team role DESCRIBE Only permission

        Parameters
        ----------
        target_environment :
        dataset :
        shared_db_name :
        principals :

        Returns
        -------
        boto3 glue create_database
        """

        logger.info(
            f'Creating shared db ...'
            f'{target_environment.AwsAccountId}://{shared_db_name}'
        )

        database = Glue.create_database(
            target_environment.AwsAccountId,
            shared_db_name,
            target_environment.region,
            f's3://{dataset.S3BucketName}',
        )

        LakeFormation.grant_pivot_role_all_database_permissions(
            target_environment.AwsAccountId, target_environment.region, shared_db_name
        )

        LakeFormation.grant_permissions_to_database(
            client=SessionHelper.remote_session(
                accountid=target_environment.AwsAccountId
            ).client('lakeformation', region_name=target_environment.region),
            principals=principals,
            database_name=shared_db_name,
            permissions=['DESCRIBE'],
        )

        return database

    def delete_shared_database(self) -> bool:
        """
        Deletes shared database when share request is rejected

        Returns
        -------
        bool
        """
        logger.info(f'Deleting shared database {self.shared_db_name}')
        return Glue.delete_database(
            accountid=self.target_environment.AwsAccountId,
            region=self.target_environment.region,
            database=self.shared_db_name,
        )

    @classmethod
    def create_resource_link(cls, **data) -> dict:
        """
        Creates a resource link to the source shared Glue table
        Parameters
        ----------
        data : data of source and target accounts

        Returns
        -------
        boto3 creation response
        """
        source = data['source']
        target = data['target']
        target_session = SessionHelper.remote_session(accountid=target['accountid'])
        lakeformation_client = target_session.client(
            'lakeformation', region_name=target['region']
        )
        target_database = target['database']
        resource_link_input = {
            'Name': source['tablename'],
            'TargetTable': {
                'CatalogId': data['source']['accountid'],
                'DatabaseName': source['database'],
                'Name': source['tablename'],
            },
        }

        try:
            resource_link = Glue.create_resource_link(
                accountid=target['accountid'],
                region=target['region'],
                database=target_database,
                resource_link_name=source['tablename'],
                resource_link_input=resource_link_input,
            )

            LakeFormation.grant_resource_link_permission(
                lakeformation_client, source, target, target_database
            )

            LakeFormation.grant_resource_link_permission_on_target(
                lakeformation_client, source, target
            )

            return resource_link

        except ClientError as e:
            logger.warning(
                f'Resource Link {resource_link_input} was not created due to: {e}'
            )
            raise e

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
            logger.info(
                f'Resource link could not be found '
                f'on {self.target_environment.AwsAccountId}/{self.shared_db_name}/{table.GlueTableName} '
                f'skipping revoke actions...'
            )
            return True

        logger.info(
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
            logger.info(
                f'Source table could not be found '
                f'on {self.source_environment.AwsAccountId}/{self.dataset.GlueDatabaseName}/{table.GlueTableName} '
                f'skipping revoke actions...'
            )
            return True

        logger.info(
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

    def delete_resource_link_table(self, table: models.DatasetTable):
        logger.info(f'Deleting shared table {table.GlueTableName}')

        if not Glue.table_exists(
                accountid=self.target_environment.AwsAccountId,
                region=self.target_environment.region,
                database=self.shared_db_name,
                tablename=table.GlueTableName,
        ):
            return True
        Glue.delete_table(
            accountid=self.target_environment.AwsAccountId,
            region=self.target_environment.region,
            database=self.shared_db_name,
            tablename=table.GlueTableName
        )
        return True

    def handle_share_failure(
        self,
        table: models.DatasetTable,
        share_item: models.ShareObjectItem,
        error: Exception,
    ) -> bool:
        """
        Handles share failure by raising an alarm to alarmsTopic
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
            f'Failed to share table {table.GlueTableName} '
            f'from source account {self.source_environment.AwsAccountId}//{self.source_environment.region} '
            f'with target account {self.target_environment.AwsAccountId}/{self.target_environment.region}'
            f'due to: {error}'
        )

        AlarmService().trigger_table_sharing_failure_alarm(
            table, self.share, self.target_environment
        )
        return True

    def handle_revoke_failure(
            self,
            table: models.DatasetTable,
            share_item: models.ShareObjectItem,
            error: Exception,
    ) -> bool:
        """
        Handles share failure by raising an alarm to alarmsTopic
        Returns
        -------
        True if alarm published successfully
        """
        logger.error(
            f'Failed to revoke S3 permissions to table {table.GlueTableName} '
            f'from source account {self.source_environment.AwsAccountId}//{self.source_environment.region} '
            f'with target account {self.target_environment.AwsAccountId}/{self.target_environment.region} '
            f'due to: {error}'
        )
        api.ShareObject.update_share_item_status(
            self.session,
            share_item,
            models.ShareItemStatus.Revoke_Failed.value,
        )
        AlarmService().trigger_revoke_sharing_failure_alarm(
            table, self.share, self.target_environment
        )
        return True