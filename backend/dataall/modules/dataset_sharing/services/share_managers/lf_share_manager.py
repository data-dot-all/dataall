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
from dataall.modules.dataset_sharing.db.share_object_models import ShareObjectItem, ShareObject, Catalog

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
        catalog: Catalog = None,
    ):
        self.session = session
        self.env_group = env_group
        self.dataset = dataset
        self.share = share
        self.shared_tables = shared_tables
        self.revoked_tables = revoked_tables
        self.source_environment = source_environment
        self.target_environment = target_environment
        self.catalog_details = catalog
        self.source_accountid = catalog.account_id if catalog else source_environment.AwsAccountId
        self.source_region = catalog.region if catalog else source_environment.region
        self.source_database_name = catalog.database_name if catalog else dataset.GlueDatabaseName
        self.principals = self.get_share_principals()
        self.shared_db_name = self.build_shared_db_name()
        self.verify_catalog_ownership()

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
        Build Glue shared database name.
        Unique per share Uri.

        Returns
        -------
        Shared database name
        """
        return (self.source_database_name + '_shared_' + self.share.shareUri)[:254]

    def build_share_data(self, table: DatasetTable) -> dict:
        """
        Build aws dict for boto3 operations on Glue and LF from share data
        Parameters
        ----------
        table : dataset table

        Returns
        -------
        dict for boto3 operations
        """

        data = {
            'source': {
                'accountid': self.source_accountid,
                'region': self.source_region,
                'database': self.source_database_name,
                'tablename': table.GlueTableName,
            },
            'target': {
                'accountid': self.target_environment.AwsAccountId,
                'region': self.target_environment.region,
                'principals': self.principals,
                'database': self.shared_db_name,
            },
        }
        return data

    def check_share_item_exists_on_glue_catalog(
        self, share_item: ShareObjectItem, table: DatasetTable
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
        glue_client = GlueClient(
            account_id=self.source_accountid,
            region=self.source_region,
            database=self.source_database_name,
        )
        if not glue_client.table_exists(table.GlueTableName):
            raise exceptions.AWSResourceNotFound(
                action='ProcessShare',
                message=(
                    f'Share Item {share_item.itemUri} found on share request'
                    f' but its correspondent Glue table {table.GlueTableName} does not exist.'
                ),
            )

    def grant_pivot_role_all_database_permissions(self) -> bool:
        """
        Grants 'ALL' database Lake Formation permissions to data.all PivotRole
        """

        LakeFormationClient.grant_pivot_role_all_database_permissions(
            self.source_accountid,
            self.source_region,
            self.source_database_name,
        )

        return True

    @classmethod
    def create_shared_database(
        cls,
        target_environment: Environment,
        dataset: Dataset,
        shared_db_name: str,
        principals: [str],
    ) -> dict:

        """
        Creates the shared database if does not exists.
        1) Grants pivot role ALL permission on shareddb
        2) Grant principals DESCRIBE Only permission

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

        database = GlueClient(
            account_id=target_environment.AwsAccountId,
            database=shared_db_name,
            region=target_environment.region
        ).create_database(f's3://{dataset.S3BucketName}')

        LakeFormationClient.grant_pivot_role_all_database_permissions(
            target_environment.AwsAccountId, target_environment.region, shared_db_name
        )

        LakeFormationClient.grant_permissions_to_database(
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
        return self.target_glue_client().delete_database()

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
            glue_client = GlueClient(target['accountid'], target['region'], target_database)
            resource_link = glue_client.create_resource_link(
                resource_link_name=source['tablename'],
                resource_link_input=resource_link_input,
            )

            LakeFormationClient.grant_resource_link_permission(
                lakeformation_client, source, target, target_database
            )

            LakeFormationClient.grant_resource_link_permission_on_target(
                lakeformation_client, source, target
            )

            return resource_link

        except ClientError as e:
            logger.warning(
                f'Resource Link {resource_link_input} was not created due to: {e}'
            )
            raise e

    def revoke_table_resource_link_access(self, table: DatasetTable, principals: [str]):
        """
        Revokes access to glue table resource link
        Parameters
        ----------
        table : DatasetTable
        principals: List of strings. IAM role arn and Quicksight groups

        Returns
        -------
        True if revoke is successful
        """
        glue_client = self.target_glue_client()
        if not glue_client.table_exists(table.GlueTableName):
            logger.info(
                f'Resource link could not be found '
                f'on {self.target_environment.AwsAccountId}/{self.shared_db_name}/{table.GlueTableName} '
                f'skipping revoke actions...'
            )
            return True

        for principal in principals:
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

    def revoke_source_table_access(self, table, principals: [str]):
        """
        Revokes access to the source glue table
        Parameters
        ----------
        table : DatasetTable

        Returns
        -------
        True if revoke is successful
        """

        glue_client = GlueClient(account_id=self.source_accountid,
                                 database=self.source_database_name,
                                 region=self.source_region)
        if not glue_client.table_exists(table.GlueTableName):
            logger.info(
                f'Source table could not be found '
                f'on {self.source_accountid}/{self.source_database_name}/{table.GlueTableName} '
                f'skipping revoke actions...'
            )
            return True

        logger.info(
            f'Revoking source table access '
            f'on {self.source_accountid}/{self.source_database_name}/{table.GlueTableName} '
            f'for principals {principals}'
        )
        LakeFormationClient.revoke_source_table_access(
            target_accountid=self.target_environment.AwsAccountId,
            region=self.target_environment.region,
            source_database=self.source_database_name,
            source_table=table.GlueTableName,
            target_principals=principals,
            source_accountid=self.source_accountid,
        )
        return True

    def delete_resource_link_table(self, table: DatasetTable):
        logger.info(f'Deleting shared table {table.GlueTableName}')
        glue_client = self.target_glue_client()

        if not glue_client.table_exists(table.GlueTableName):
            return True

        glue_client.delete_table(table.GlueTableName)
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

            LakeFormationClient.revoke_iamallowedgroups_super_permission_from_table(
                source_lf_client,
                source_accountid,
                data['source']['database'],
                data['source']['tablename'],
            )

            glue_client = GlueClient(source_accountid, source_region, data['source']['database'])
            glue_client.remove_create_table_default_permissions()
            time.sleep(1)

            LakeFormationClient.grant_permissions_to_table(
                source_lf_client,
                target_accountid,
                data['source']['database'],
                data['source']['tablename'],
                ['DESCRIBE', 'SELECT'],
                ['DESCRIBE', 'SELECT'],
            )
            time.sleep(2)

            logger.info(
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

    def revoke_external_account_access_on_source_account(self, db_name, table_name) -> [dict]:
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
            accountid=self.source_accountid
        )
        client = aws_session.client(
            'lakeformation', region_name=self.source_region
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
                            'DatabaseName': self.source_database_name,
                            'Name': table.GlueTableName,
                            'ColumnWildcard': {},
                            'CatalogId': self.source_accountid,
                        }
                    },
                    'Permissions': ['DESCRIBE', 'SELECT'],
                    'PermissionsWithGrantOption': ['DESCRIBE', 'SELECT'],
                }
            )
            LakeFormationClient.batch_revoke_permissions(
                client, self.source_accountid, revoke_entries
            )
        return revoke_entries

    def handle_share_failure(
        self,
        table: DatasetTable,
        share_item: ShareObjectItem,
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
            f'from source account {self.source_accountid}//{self.source_region} '
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
            share_item: ShareObjectItem,
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
            f'from source account {self.source_accountid}//{self.source_region} '
            f'with target account {self.target_environment.AwsAccountId}/{self.target_environment.region} '
            f'due to: {error}'
        )
        DatasetAlarmService().trigger_revoke_table_sharing_failure_alarm(
            table, self.share, self.target_environment
        )
        return True

    def target_glue_client(self):
        return GlueClient(
            account_id=self.target_environment.AwsAccountId,
            region=self.target_environment.region,
            database=self.shared_db_name,
        )

    def verify_catalog_ownership(self):
        if self.catalog_details is None:
            logger.info(f'database {self.dataset.GlueDatabaseName} is not a resource link, no catalog information present')
            return

        if self.catalog_details.account_id != self.source_environment.AwsAccountId:
            logger.info(f'database {self.dataset.GlueDatabaseName} is a resource link '
                        f'the source database {self.catalog_details.database_name} belongs to a catalog account {self.catalog_details.account_id}')
            if SessionHelper.is_assumable_pivot_role(self.catalog_details.account_id):
                self.validate_catalog_ownership_tag()
            else:
                raise Exception(f'Pivot role is not assumable, catalog account {self.catalog_details.account_id} is not onboarded')

    def validate_catalog_ownership_tag(self):
        glue_client = GlueClient(account_id=self.catalog_details.account_id,
                                 database=self.catalog_details.database_name,
                                 region=self.catalog_details.region)
        tags = glue_client.get_database_tags()
        if tags.get('owner_account_id', '') == self.source_environment.AwsAccountId:
            logger.info(f'owner_account_id tag exists and matches the source account id {self.source_environment.AwsAccountId}')
        else:
            raise Exception(f'owner_account_id tag does not exist or does not matches the source account id {self.source_environment.AwsAccountId}')
