import abc
import logging
import time
from warnings import warn

from dataall.core.environment.db.environment_models import Environment, EnvironmentGroup
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.modules.dataset_sharing.aws.glue_client import GlueClient
from dataall.modules.dataset_sharing.aws.lakeformation_client import LakeFormationClient
from dataall.base.aws.quicksight import QuicksightClient
from dataall.base.aws.iam import IAM
from dataall.base.aws.sts import SessionHelper
from dataall.base.db import exceptions
from dataall.modules.dataset_sharing.db.share_object_repositories import ShareObjectRepository, ShareItemSM
from dataall.modules.dataset_sharing.services.dataset_sharing_enums import ShareItemStatus, ShareObjectActions, \
    ShareItemActions
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
        self.source_account_id = source_environment.AwsAccountId
        self.source_account_region = source_environment.region
        self.source_database_name = dataset.GlueDatabaseName
        self.shared_db_name, self.is_new_share = self.build_shared_db_name()
        self.principals = self.get_share_principals()
        self.cross_account = self.target_environment.AwsAccountId != self.source_account_id
        self.lf_client_in_target = LakeFormationClient(
            account_id=self.target_environment.AwsAccountId,
            region=self.target_environment.region
        )
        self.lf_client_in_source = LakeFormationClient(
            account_id=self.source_account_id,
            region=self.source_account_region
        )
        self.glue_client_in_target = GlueClient(
            account_id=self.target_environment.AwsAccountId,
            region=self.target_environment.region,
            database=self.shared_db_name,
        )
        self.glue_client_in_source = GlueClient(
            account_id=self.source_account_id,
            region=self.source_account_region,
            database=self.source_database_name,
        )

    @abc.abstractmethod
    def process_approved_shares(self) -> [str]:
        return NotImplementedError

    @abc.abstractmethod
    def process_revoked_shares(self) -> [str]:
        return NotImplementedError

    def get_share_principals(self) -> [str]:
        """
        Builds list of principals of the share request
        :return: List of principals' arns
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

    def build_shared_db_name(self) -> tuple:
        """
        It checks if a share is prior to 2.3.0 and builds its suffix as "_shared_" + shareUri
        For shares after 2.3.0 the suffix returned is "_shared"
        :return: Shared database name, boolean indicating if it is a new share
        """
        old_shared_db_name = (self.source_database_name + '_shared_' + self.share.shareUri)[:254]
        warn('old_shared_db_name will be deprecated in v2.6.0', DeprecationWarning, stacklevel=2)
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
        return self.source_database_name + '_shared', True

    def check_table_exists_in_source_database(
        self, share_item: ShareObjectItem, table: DatasetTable
    ) -> True:
        """
        Checks if the table to be shared exists on the Glue catalog in the source account
        :param share_item: request share item
        :param table: DatasetTable
        :return: True or raise exceptions.AWSResourceNotFound
        """
        if not self.glue_client_in_source.table_exists(table.GlueTableName):
            raise exceptions.AWSResourceNotFound(
                action='ProcessShare',
                message=(
                    f'Share Item {share_item.itemUri} found on share request'
                    f' but its correspondent Glue table {table.GlueTableName} does not exist.'
                ),
            )
        return True

    def check_resource_link_table_exists_in_target_database(
        self, table: DatasetTable
    ) -> bool:
        """
        Checks if the table to be shared exists on the Glue catalog in the target account as resource link
        :param table: DatasetTable
        :return: Boolean
        """
        if self.glue_client_in_target.table_exists(table.GlueTableName):
            return True
        logger.info(
            f'Resource link could not be found '
            f'on {self.target_environment.AwsAccountId}/{self.shared_db_name}/{table.GlueTableName} '
        )
        return False

    def revoke_iam_allowed_principals_from_table(self, table: DatasetTable) -> True:
        """
        Revoke ALL permissions to IAMAllowedPrincipal to the original table in source account.
        Needed for cross-account permissions. Unless this is revoked the table cannot be shared using LakeFormation
        :param table: DatasetTable
        :return: True if it is successful
        """
        self.lf_client_in_source.revoke_permissions_from_table(
            principals=['EVERYONE'],
            database_name=self.source_database_name,
            table_name=table.GlueTableName,
            catalog_id=self.source_account_id,
            permissions=['ALL']
        )
        return True

    def grant_pivot_role_all_database_permissions_to_source_database(self) -> True:
        """
        Grants 'ALL' Lake Formation permissions to data.all PivotRole to the original database in source account
        :return: True if it is successful
        """
        self.lf_client_in_source.grant_permissions_to_database(
            principals=[SessionHelper.get_delegation_role_arn(self.source_account_id)],
            database_name=self.source_database_name,
            permissions=['ALL'],
        )
        return True

    def check_if_exists_and_create_shared_database_in_target(self) -> dict:
        """
        Checks if shared database exists in target account
        Creates the shared database if it does not exist
        :return: boto3 glue create_database
        """

        database = self.glue_client_in_target.create_database(location=f's3://{self.dataset.S3BucketName}')
        return database

    def grant_pivot_role_all_database_permissions_to_shared_database(self) -> True:
        """
        Grants 'ALL' Lake Formation permissions to data.all PivotRole to the shared database in target account
        :return: True if it is successful
        """
        self.lf_client_in_target.grant_permissions_to_database(
            principals=[SessionHelper.get_delegation_role_arn(self.target_environment.AwsAccountId)],
            database_name=self.shared_db_name,
            permissions=['ALL'],
        )
        return True

    def grant_pivot_role_drop_permissions_to_resource_link_table(self, table: DatasetTable) -> True:
        """
        Grants 'DROP' Lake Formation permissions to pivot role to the resource link table in target account
        :param table: DatasetTable
        :return: True if it is successful
        """
        self.lf_client_in_target.grant_permissions_to_table(
            principals=[SessionHelper.get_delegation_role_arn(self.target_environment.AwsAccountId)],
            database_name=self.shared_db_name,
            table_name=table.GlueTableName,
            catalog_id=self.target_environment.AwsAccountId,
            permissions=['DROP']
        )
        return True

    def grant_principals_database_permissions_to_shared_database(self) -> True:
        """
        Grants 'DESCRIBE' Lake Formation permissions to share principals to the shared database in target account
        :return: True if it is successful
        """
        self.lf_client_in_target.grant_permissions_to_database(
            principals=self.principals,
            database_name=self.shared_db_name,
            permissions=['DESCRIBE'],
        )
        return True

    def grant_target_account_permissions_to_source_table(self, table: DatasetTable) -> True:
        """
        Grants 'DESCRIBE' 'SELECT' Lake Formation permissions to target account to the original table in source account
        :param table: DatasetTable
        :return: True if it is successful
        """
        self.lf_client_in_source.grant_permissions_to_table(
            principals=[self.target_environment.AwsAccountId],
            database_name=self.source_database_name,
            table_name=table.GlueTableName,
            catalog_id=self.source_account_id,
            permissions=['DESCRIBE', 'SELECT'],
            permissions_with_grant_options=['DESCRIBE', 'SELECT']
        )
        time.sleep(2)
        return True

    def check_if_exists_and_create_resource_link_table_in_shared_database(self, table: DatasetTable) -> True:
        """
        Checks if resource link to the source shared Glue table exists in target account
        Creates a resource link if it does not exist
        :param table: DatasetTable
        :return: True if it is successful
        """
        if not self.check_resource_link_table_exists_in_target_database(table):
            self.glue_client_in_target.create_resource_link(
                resource_link_name=table.GlueTableName,
                table=table,
                catalog_id=self.source_account_id,
                database=self.source_database_name
            )
        return True

    def grant_principals_permissions_to_resource_link_table(self, table: DatasetTable) -> True:
        """
        Grants 'DESCRIBE' Lake Formation permissions to share principals to the resource link table in target account
        :param table: DatasetTable
        :return: True if it is successful
        """
        self.lf_client_in_target.grant_permissions_to_table(
            principals=self.principals,
            database_name=self.shared_db_name,
            table_name=table.GlueTableName,
            catalog_id=self.target_environment.AwsAccountId,
            permissions=['DESCRIBE']
        )
        return True

    def grant_principals_permissions_to_table_in_target(self, table: DatasetTable) -> True:
        """
        Grants 'DESCRIBE', 'SELECT' Lake Formation permissions to share principals to the table shared in target account
        :param table: DatasetTable
        :return: True if it is successful
        """
        self.lf_client_in_target.grant_permissions_to_table_with_columns(
            principals=self.principals,
            database_name=self.source_database_name,
            table_name=table.GlueTableName,
            catalog_id=self.source_account_id,
            permissions=['DESCRIBE', 'SELECT']
        )
        return True

    def revoke_principals_permissions_to_resource_link_table(self, table: DatasetTable) -> True:
        """
        Revokes 'DESCRIBE' Lake Formation permissions to share principals to the resource link table in target account
        At the moment there is one single Quicksight group per environment. Permissions for the Quicksight group
        are removed when the resource link table is deleted.
        :param table: DatasetTable
        :return: True if it is successful
        """
        principals = [p for p in self.principals if "arn:aws:quicksight" not in p]

        self.lf_client_in_target.revoke_permissions_from_table(
            principals=principals,
            database_name=self.shared_db_name,
            table_name=table.GlueTableName,
            catalog_id=self.target_environment.AwsAccountId,
            permissions=['DESCRIBE']
        )
        return True

    def revoke_principals_permissions_to_table_in_target(self, table: DatasetTable, other_table_shares_in_env) -> True:
        """
        Revokes 'DESCRIBE', 'SELECT' Lake Formation permissions to share principals to the table shared in target account
        If there are no more shares for this table in the environment then revoke to Quicksight group
        :param table: DatasetTable
        :param other_table_shares_in_env: Boolean. Other table shares in this environment for this table
        :return: True if it is successful
        """
        principals = self.principals if not other_table_shares_in_env else [p for p in self.principals if "arn:aws:quicksight" not in p]

        self.lf_client_in_target.revoke_permissions_from_table_with_columns(
            principals=principals,
            database_name=self.source_database_name,
            table_name=table.GlueTableName,
            catalog_id=self.source_account_id,
            permissions=['DESCRIBE', 'SELECT']
        )
        return True

    def revoke_principals_database_permissions_to_shared_database(self) -> True:
        """
        Revokes 'DESCRIBE' Lake Formation permissions to share principals to the shared database in target account
        At the moment there is one single Quicksight group per environment. Permissions for the Quicksight group
        are removed when the database is deleted.
        :return: True if it is successful
        """
        principals = [p for p in self.principals if "arn:aws:quicksight" not in p]

        self.lf_client_in_target.revoke_permissions_to_database(
            principals=principals,
            database_name=self.shared_db_name,
            permissions=['DESCRIBE'],
        )
        return True

    def delete_resource_link_table_in_shared_database(self, table: DatasetTable) -> True:
        """
        Checks if resource link table from shared database in target account exists
        Deletes it if it exists
        :param table: DatasetTable
        :return: True if it is successful
        """
        glue_client = self.glue_client_in_target
        if not glue_client.table_exists(table.GlueTableName):
            return True

        glue_client.delete_table(table.GlueTableName)
        return True

    def delete_shared_database_in_target(self) -> True:
        """
        Checks if shared database in target account exists
        Deletes it if it exists
        :return: True if it is successful
        """
        logger.info(f'Deleting shared database {self.shared_db_name}')
        self.glue_client_in_target.delete_database()
        return True

    def revoke_external_account_access_on_source_account(self, table: DatasetTable) -> True:
        """
        Revokes 'DESCRIBE' 'SELECT' Lake Formation permissions to target account to the original table in source account
        If the table is not shared with any other team in the environment,
        it deletes resource_shares on RAM associated to revoked table
        :param table: DatasetTable
        :return: True if it is successful
        """
        self.lf_client_in_source.revoke_permissions_from_table_with_columns(
            principals=[self.target_environment.AwsAccountId],
            database_name=self.source_database_name,
            table_name=table.GlueTableName,
            catalog_id=self.source_account_id,
            permissions=['DESCRIBE', 'SELECT'],
            permissions_with_grant_options=['DESCRIBE', 'SELECT']
        )
        return True

    def handle_share_failure(
        self,
        table: DatasetTable,
        error: Exception,
    ) -> True:
        """
        Handles share failure by raising an alarm to alarmsTopic
        :param table: DatasetTable
        :param error: share error
        :return: True if alarm published successfully
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
    ) -> True:
        """
        Handles share failure by raising an alarm to alarmsTopic
        :param table: DatasetTable
        :param error: share error
        :return: True if alarm published successfully
        """
        logger.error(
            f'Failed to revoke Lake Formation permissions to table {table.GlueTableName} '
            f'from source account {self.source_environment.AwsAccountId}//{self.source_environment.region} '
            f'with target account {self.target_environment.AwsAccountId}/{self.target_environment.region} '
            f'due to: {error}'
        )
        DatasetAlarmService().trigger_revoke_table_sharing_failure_alarm(
            table, self.share, self.target_environment
        )
        return True

    def handle_share_failure_for_all_tables(self, tables, error, share_item_status):
        for table in tables:
            share_item = ShareObjectRepository.find_sharable_item(
                self.session, self.share.shareUri, table.tableUri
            )
            share_item_sm = ShareItemSM(share_item_status)
            new_state = share_item_sm.run_transition(ShareObjectActions.Start.value)
            share_item_sm.update_state_single_item(self.session, share_item, new_state)
            new_state = share_item_sm.run_transition(ShareItemActions.Failure.value)
            share_item_sm.update_state_single_item(self.session, share_item, new_state)

            self.handle_revoke_failure(table=table, error=error)

    def verify_catalog_ownership(self, catalog_dict):
        if catalog_dict.get('account_id') != self.source_environment.AwsAccountId:
            logger.info(f'Database {self.dataset.GlueDatabaseName} is a resource link and '
                        f'the source database {catalog_dict.get("database_name")} belongs to a catalog account {catalog_dict.get("account_id")}')
            if SessionHelper.is_assumable_pivot_role(catalog_dict.get('account_id')):
                self.validate_catalog_ownership_tag(catalog_dict)
            else:
                raise Exception(f'Pivot role is not assumable, catalog account {catalog_dict.get("account_id")} is not onboarded')

    def validate_catalog_ownership_tag(self, catalog_dict):
        glue_client = GlueClient(account_id=catalog_dict.get('account_id'),
                                 database=catalog_dict.get('database_name'),
                                 region=catalog_dict.get('region'))

        tags = glue_client.get_database_tags()
        if tags.get('owner_account_id', '') == self.source_environment.AwsAccountId:
            logger.info(f'owner_account_id tag exists and matches the source account id {self.source_environment.AwsAccountId}')
        else:
            raise Exception(f'owner_account_id tag does not exist or does not matches the source account id {self.source_environment.AwsAccountId}')

    def check_catalog_account_exists_and_update_processor(self):
        try:
            catalog_dict = self.glue_client_in_source.get_source_catalog()
            if catalog_dict is not None:
                # Found a catalog account
                logger.info("Updating source aws account id, source account region, source database with catalog details")
                logger.debug(f"Catalog Account id - {catalog_dict.get('account_id')}, Catalog Region - { catalog_dict.get('region')}, Catalog DB - {catalog_dict.get('database_name')}")
                self.source_account_id = catalog_dict.get('account_id')
                self.source_account_region = catalog_dict.get('region')
                self.source_database_name = catalog_dict.get('database_name')
                # Build the shared db name again as the shared db name on the producer account cannot be used ( as that is the resource link ).
                # Instead update the shared db name with the new name.
                self.shared_db_name, self.is_new_share = self.build_shared_db_name()
                # Again Update the Cross Account Instance Variable
                self.cross_account = self.target_environment.AwsAccountId != self.source_account_id
                # Update / Reinitialize Glue and Lake formation Clients as the source account , region, db are changed
                # Also reinitialize target glue client as the shared DB name changes
                self.lf_client_in_source = LakeFormationClient(
                    account_id=self.source_account_id,
                    region=self.source_account_region
                )
                self.glue_client_in_source = GlueClient(
                    account_id=self.source_account_id,
                    region=self.source_account_region,
                    database=self.source_database_name,
                )

                self.glue_client_in_target = GlueClient(
                    account_id=self.target_environment.AwsAccountId,
                    region=self.target_environment.region,
                    database=self.shared_db_name,
                )

                # Verify the ownership of dataset
                self.verify_catalog_ownership(catalog_dict)
            else:
                logger.info(
                    f'No Catalog information found for dataset - {self.dataset.name} containing database - {self.dataset.GlueDatabaseName}')

            return True

        except Exception as e:
            logger.error(
                f'Failed to initialise catalog account details for share - {self.share.shareUri} '
                f'due to: {e}'
            )
            raise e
