import abc
import logging
import uuid
import time

from botocore.exceptions import ClientError

from dataall.core.environment.db.environment_models import Environment, EnvironmentGroup
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.modules.dataset_sharing.aws.glue_client import GlueClient
from dataall.modules.dataset_sharing.aws.lakeformation_client import LakeFormationClient
from dataall.base.aws.quicksight import QuicksightClient
from dataall.base.aws.iam import IAM
from dataall.base.aws.sts import SessionHelper
from dataall.base.db import exceptions
from dataall.modules.datasets_base.db.dataset_models import DatasetTable, Dataset
from dataall.modules.dataset_sharing.services.dataset_alarm_service import DatasetAlarmService
from dataall.modules.dataset_sharing.db.share_object_models import ShareObjectItem, ShareObject

logger = logging.getLogger(__name__)


class LFShareManager:
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
        self.session = session
        self.env_group = env_group
        self.dataset = dataset
        self.share = share
        self.shared_tables = shared_tables
        self.revoked_tables = revoked_tables
        self.source_environment = source_environment
        self.target_environment = target_environment
        self.shared_db_name, self.is_new_share = self.build_shared_db_name()
        self.principals = self.get_share_principals()
        self.cross_account = True if self.target_environment.AwsAccountId != self.source_environment.AwsAccountId else False

    @abc.abstractmethod
    def process_approved_shares(self) -> [str]:
        return NotImplementedError

    @abc.abstractmethod
    def process_revoked_shares(self) -> [str]:
        return NotImplementedError

    def get_share_principals(self) -> [str]:
        """
        Builds list of principals of the share request
        Returns
        -------
        List of principals
        """
        principal_iam_role_arn = IAM.get_role_arn_by_name(
            account_id=self.target_environment.AwsAccountId,
            role_name=self.share.principalIAMRoleName
        )
        principals = [principal_iam_role_arn]
        dashboard_enabled = EnvironmentService.get_boolean_env_param(self.session, self.target_environment, "dashboardsEnabled")

        if dashboard_enabled:
            group = QuicksightClient.create_quicksight_group(
                AwsAccountId=self.target_environment.AwsAccountId, region=self.target_environment.region
            )
            if group and group.get('Group'):
                group_arn = group.get('Group').get('Arn')
                if group_arn:
                    principals.append(group_arn)

        return principals

    def build_shared_db_name(self) -> str:
        """
        It checks if a share is prior to 2.3.0 and builds its suffix as "_shared + shareUri"
        For shares after 2.3.0 the suffix returned is "_shared"
        Returns
        -------
        Shared database name
        """
        old_shared_db_name = (self.dataset.GlueDatabaseName + '_shared_' + self.share.shareUri)[:254]
        logger.info(
            f'Checking shared db {old_shared_db_name} exists in {self.target_environment.AwsAccountId}...'
        )
        database = GlueClient(
            account_id=self.target_environment.AwsAccountId,
            database=old_shared_db_name,
            region=self.target_environment.region
        ).get_glue_database()

        if database:
            return old_shared_db_name, False
        return self.dataset.GlueDatabaseName[:247] + '_shared', True

    def check_table_exists_in_source_database(
        self, share_item: ShareObjectItem, table: DatasetTable
    ) -> None:
        """
        Checks if a table in the share request
        still exists on the Glue catalog in the source account before sharing

        Parameters
        ----------
        share_item : request share item
        table : dataset table

        Returns
        -------
        exceptions.AWSResourceNotFound
        """
        glue_client = GlueClient(
            account_id=self.source_environment.AwsAccountId,
            region=self.source_environment.region,
            database=table.GlueDatabaseName,
        )
        if not glue_client.table_exists(table.GlueTableName):
            raise exceptions.AWSResourceNotFound(
                action='ProcessShare',
                message=(
                    f'Share Item {share_item.itemUri} found on share request'
                    f' but its correspondent Glue table {table.GlueTableName} does not exist.'
                ),
            )

    def check_resource_link_table_exists_in_target_database(
        self, table: DatasetTable
    ) -> None:
        """
        Checks if a table in the share request
        exists on the Glue catalog in the target account as resource link

        Parameters
        ----------
        table : dataset table

        Returns
        -------
        Boolean
        """
        glue_client = GlueClient(
            account_id=self.target_environment.AwsAccountId,
            region=self.target_environment.region,
            database=self.shared_db_name,
        )
        if glue_client.table_exists(table.GlueTableName):
            return True
        logger.info(
            f'Resource link could not be found '
            f'on {self.target_environment.AwsAccountId}/{self.shared_db_name}/{table.GlueTableName} '
        )
        return False


    def grant_pivot_role_all_database_permissions_to_source_database(self) -> bool:
        """
        Grants 'ALL' database Lake Formation permissions to data.all PivotRole in source account
        Returns
        -------
        True if it is successful
        """
        LakeFormationClient.grant_permissions_to_database(
            client=SessionHelper.remote_session(accountid=self.source_environment.AwsAccountId).client(
                'lakeformation', region_name=self.source_environment.region
            ),
            principals=[SessionHelper.get_delegation_role_arn(self.source_environment.AwsAccountId)],
            database_name=self.dataset.GlueDatabaseName,
            permissions=['ALL'],
        )
        return True


    def check_if_exists_and_create_shared_database_in_target(self) -> dict:
        """
        Checks if shared database exists in target account
        Creates the shared database if it does not exist

        Returns
        -------
        boto3 glue create_database
        """

        logger.info(
            f'Creating shared db ...'
            f'{self.target_environment.AwsAccountId}://{self.shared_db_name}'
        )
        glue_client = self._glue_client_in_target()
        database = glue_client.create_database(f's3://{self.dataset.S3BucketName}')

        return database

    def grant_pivot_role_all_database_permissions_to_shared_database(self):
        LakeFormationClient.grant_permissions_to_database(
            client=SessionHelper.remote_session(accountid=self.target_environment.AwsAccountId).client(
                'lakeformation', region_name=self.target_environment.region
            ),
            principals=[SessionHelper.get_delegation_role_arn(self.target_environment.AwsAccountId)],
            database_name=self.shared_db_name,
            permissions=['ALL'],
        )
        return True

    def grant_principals_database_permissions_to_shared_database(self):
        LakeFormationClient.grant_permissions_to_database(
            client=SessionHelper.remote_session(
                accountid=self.target_environment.AwsAccountId
            ).client('lakeformation', region_name=self.target_environment.region),
            principals=self.principals,
            database_name=self.shared_db_name,
            permissions=['DESCRIBE'],
        )
        return True

    def delete_shared_database_in_target(self) -> bool:
        """
        Deletes shared database when share request is rejected

        Returns
        -------
        bool
        """
        logger.info(f'Deleting shared database {self.shared_db_name}')
        return self._glue_client_in_target().delete_database()

    def check_if_exists_and_create_resource_link_table_in_shared_database(self, table: DatasetTable) -> dict:
        """
        Creates a resource link to the source shared Glue table
        Parameters
        ----------
        table : DatasetTable

        Returns
        -------
        Boolean
        """

        glue_client = self._glue_client_in_target()
        if not self.check_resource_link_table_exists_in_target_database(table):
            logger.info(
                f'Creating resource link table ...'
                f'in {self.target_environment.AwsAccountId}/{self.shared_db_name}/{table.GlueTableName}'
            )
            try:
                resource_link_input = {
                    'Name': table.GlueTableName,
                    'TargetTable': {
                        'CatalogId': self.source_environment.AwsAccountId,
                        'DatabaseName': table.GlueDatabaseName,
                        'Name': table.GlueTableName,
                    },
                }
                glue_client.create_resource_link(
                    resource_link_name=table.GlueTableName,
                    resource_link_input=resource_link_input,
                )
                return True

            except ClientError as e:
                logger.warning(
                    f'Resource Link {resource_link_input} was not created due to: {e}'
                )
                raise e

    def grant_principals_permissions_to_resource_link_table(self, table: DatasetTable):
        target_session = SessionHelper.remote_session(accountid=self.target_environment.AwsAccountId)
        lakeformation_client = target_session.client(
            'lakeformation', region_name=self.target_environment.region
        )
        LakeFormationClient.grant_permissions_to_resource_link_table(
            client=lakeformation_client,
            table_name=table.GlueTableName,
            target_database=self.shared_db_name,
            target_account=self.target_environment.AwsAccountId,
            principals=self.principals
        )

    def grant_principals_permissions_to_table_in_target(self, table: DatasetTable):
        target_session = SessionHelper.remote_session(accountid=self.target_environment.AwsAccountId)
        lakeformation_client = target_session.client(
            'lakeformation', region_name=self.target_environment.region
        )
        LakeFormationClient.grant_permissions_to_table(
            client=lakeformation_client,
            source_account_id=self.source_environment.AwsAccountId,
            source_database=table.GlueDatabaseName,
            table_name=table.GlueTableName,
            principals=self.principals
        )

    def revoke_principals_permissions_to_resource_link_table(self, table: DatasetTable):
        """
        Revokes access to glue table resource link
        Parameters
        ----------
        table : DatasetTable

        Returns
        -------
        True if revoke is successful
        """
        for principal in self.principals:
            logger.info(
                f'Revoking resource link access '
                f'on {self.target_environment.AwsAccountId}/{self.shared_db_name}/{table.GlueTableName} '
                f'for principal {principal}'

            )
            LakeFormationClient.batch_revoke_permissions(
                SessionHelper.remote_session(self.target_environment.AwsAccountId).client(
                    'lakeformation', region_name=self.target_environment.region
                ),
                self.target_environment.AwsAccountId,
                [
                    {
                        'Id': str(uuid.uuid4()),
                        'Principal': {
                            'DataLakePrincipalIdentifier': principal
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

    def revoke_principals_permissions_to_table_in_target(self, table):
        """
        Revokes access to the source glue table
        Parameters
        ----------
        table : DatasetTable

        Returns
        -------
        True if revoke is successful
        """
        principals = [p for p in self.principals if "arn:aws:quicksight" not in p]

        logger.info(
            f'Revoking source table access '
            f'on {self.source_environment.AwsAccountId}/{self.dataset.GlueDatabaseName}/{table.GlueTableName} '
            f'for principals {principals}'
        )
        LakeFormationClient.revoke_source_table_access(
            target_accountid=self.target_environment.AwsAccountId,
            region=self.target_environment.region,
            source_database=self.dataset.GlueDatabaseName,
            source_table=table.GlueTableName,
            target_principals=principals,
            source_accountid=self.source_environment.AwsAccountId,
        )
        return True

    def delete_resource_link_table_in_shared_database(self, table: DatasetTable):
        logger.info(f'Deleting shared table {table.GlueTableName}')
        glue_client = self._glue_client_in_target()
        if not glue_client.table_exists(table.GlueTableName):
            return True

        glue_client.delete_table(table.GlueTableName)
        return True

    def share_table_with_target_account(self, table: DatasetTable):
        """
        Shares tables using Lake Formation
        Sharing feature may take some extra seconds
        :param data:
        :return:
        """

        source_session = SessionHelper.remote_session(accountid=self.source_environment.AwsAccountId)
        source_lf_client = source_session.client(
            'lakeformation', region_name=self.source_environment.region
        )
        try:
            LakeFormationClient.revoke_iamallowedgroups_super_permission_from_table(
                source_lf_client,
                self.source_environment.AwsAccountId,
                table.GlueDatabaseName,
                table.GlueTableName,
            )
            time.sleep(1)

            LakeFormationClient.grant_permissions_to_table(
                source_lf_client,
                self.target_environment.AwsAccountId, #TODO:replace it by target IAM role!
                table.GlueDatabaseName,
                table.GlueTableName,
                ['DESCRIBE', 'SELECT'],
                ['DESCRIBE', 'SELECT'],
            )
            time.sleep(2)

            logger.info(
                f"Granted access to table {table.GlueTableName} "
                f'to external account {self.target_environment.AwsAccountId} '
            )
            return True

        except ClientError as e:
            logging.error(
                f'Failed granting access to table {table.GlueTableName} '
                f'from {self.source_environment.AwsAccountId} / {self.source_environment.region} '
                f'to external account{self.target_environment.AwsAccountId}/{self.target_environment.region}'
                f'due to: {e}'
            )
            raise e

    def revoke_external_account_access_on_source_account(self, table: DatasetTable) -> [dict]:
        """
        1) Revokes access to external account
        if dataset is not shared with any other team from the same workspace
        2) Deletes resource_shares on RAM associated to revoked tables

        Returns
        -------
        List of revoke entries
        """
        logger.info(
            f'Revoking Access for AWS account: {self.target_environment.AwsAccountId}'
        )
        aws_session = SessionHelper.remote_session(
            accountid=self.source_environment.AwsAccountId
        )
        client = aws_session.client(
            'lakeformation', region_name=self.source_environment.region
        )
        revoke_entries = [
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
        ]

        LakeFormationClient.batch_revoke_permissions(
            client, self.source_environment.AwsAccountId, revoke_entries
        )
        return revoke_entries

    def handle_share_failure(
        self,
        table: DatasetTable,
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

        DatasetAlarmService().trigger_table_sharing_failure_alarm(
            table, self.share, self.target_environment
        )
        return True

    def handle_revoke_failure(
            self,
            table: DatasetTable,
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
        DatasetAlarmService().trigger_revoke_table_sharing_failure_alarm(
            table, self.share, self.target_environment
        )
        return True

    def _glue_client_in_target(self):
        return GlueClient(
            account_id=self.target_environment.AwsAccountId,
            region=self.target_environment.region,
            database=self.shared_db_name,
        )
