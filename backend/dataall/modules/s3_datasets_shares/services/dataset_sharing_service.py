from warnings import warn
from dataall.base.db import utils
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyService
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.base.context import get_context
from dataall.base.db import exceptions
from dataall.base.aws.sts import SessionHelper
from dataall.modules.shares_base.db.share_object_models import ShareObject
from dataall.modules.s3_datasets_shares.db.share_object_repositories import S3ShareObjectRepository
from dataall.modules.shares_base.db.share_object_repositories import ShareObjectRepository
from dataall.modules.shares_base.db.share_object_state_machines import ShareItemSM
from dataall.modules.shares_base.services.share_permissions import SHARE_OBJECT_APPROVER, GET_SHARE_OBJECT
from dataall.modules.s3_datasets_shares.services.share_item_service import S3ShareItemService
from dataall.modules.shares_base.services.share_item_service import ShareItemService
from dataall.modules.s3_datasets.db.dataset_repositories import DatasetRepository
from dataall.modules.s3_datasets.services.dataset_permissions import (
    MANAGE_DATASETS,
    UPDATE_DATASET,
    DELETE_DATASET,
    DELETE_DATASET_TABLE,
    DELETE_DATASET_FOLDER,
    CREDENTIALS_DATASET,
)
from dataall.modules.datasets_base.services.datasets_enums import DatasetRole, DatasetTypes
from dataall.modules.datasets_base.services.dataset_service_interface import DatasetServiceInterface
from dataall.modules.s3_datasets_shares.aws.glue_client import GlueClient


import logging

log = logging.getLogger(__name__)


class DatasetSharingService(DatasetServiceInterface):
    @property
    def dataset_type(self):
        return DatasetTypes.S3

    @staticmethod
    def resolve_additional_dataset_user_role(session, uri, username, groups):
        """Implemented as part of the DatasetServiceInterface"""
        share = S3ShareObjectRepository.get_share_by_dataset_attributes(session, uri, username, groups)
        if share is not None:
            return DatasetRole.Shared.value
        return None

    @staticmethod
    def check_before_delete(session, uri, **kwargs):
        """Implemented as part of the DatasetServiceInterface"""
        action = kwargs.get('action')
        if action in [DELETE_DATASET_FOLDER, DELETE_DATASET_TABLE]:
            has_share = S3ShareObjectRepository.has_shared_items(session, uri)
            if has_share:
                raise exceptions.ResourceShared(
                    action=action,
                    message='Revoke all shares for this item before deletion',
                )
        elif action in [DELETE_DATASET]:
            shares = S3ShareObjectRepository.list_dataset_shares_with_existing_shared_items(
                session=session, dataset_uri=uri
            )
            if shares:
                raise exceptions.ResourceShared(
                    action=DELETE_DATASET,
                    message='Revoke all dataset shares before deletion.',
                )
        else:
            raise exceptions.RequiredParameter('Delete action')
        return True

    @staticmethod
    def execute_on_delete(session, uri, **kwargs):
        """Implemented as part of the DatasetServiceInterface"""
        action = kwargs.get('action')
        if action in [DELETE_DATASET_FOLDER, DELETE_DATASET_TABLE]:
            S3ShareObjectRepository.delete_shares(session, uri)
        elif action in [DELETE_DATASET]:
            S3ShareObjectRepository.delete_shares_with_no_shared_items(session, uri)
        else:
            raise exceptions.RequiredParameter('Delete action')
        return True

    @staticmethod
    def append_to_list_user_datasets(session, username, groups):
        """Implemented as part of the DatasetServiceInterface"""
        return S3ShareObjectRepository.query_user_shared_datasets(session, username, groups)

    @staticmethod
    def extend_attach_steward_permissions(session, dataset, new_stewards, **kwargs):
        """Implemented as part of the DatasetServiceInterface"""
        dataset_shares = S3ShareObjectRepository.find_dataset_shares(session, dataset.datasetUri)
        if dataset_shares:
            for share in dataset_shares:
                ResourcePolicyService.attach_resource_policy(
                    session=session,
                    group=new_stewards,
                    permissions=SHARE_OBJECT_APPROVER,
                    resource_uri=share.shareUri,
                    resource_type=ShareObject.__name__,
                )
                if dataset.stewards != dataset.SamlAdminGroupName:
                    ResourcePolicyService.delete_resource_policy(
                        session=session,
                        group=dataset.stewards,
                        resource_uri=share.shareUri,
                    )

    @staticmethod
    def extend_delete_steward_permissions(session, dataset, **kwargs):
        """Implemented as part of the DatasetServiceInterface"""
        dataset_shares = S3ShareObjectRepository.find_dataset_shares(session, dataset.datasetUri)
        if dataset_shares:
            for share in dataset_shares:
                if dataset.stewards != dataset.SamlAdminGroupName:
                    ResourcePolicyService.delete_resource_policy(
                        session=session,
                        group=dataset.stewards,
                        resource_uri=share.shareUri,
                    )

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_DATASETS)
    @ResourcePolicyService.has_resource_permission(UPDATE_DATASET)
    def verify_dataset_share_objects(uri: str, share_uris: list):
        with get_context().db_engine.scoped_session() as session:
            for share_uri in share_uris:
                share = ShareObjectRepository.get_share_by_uri(session, share_uri)
                states = ShareItemSM.get_share_item_revokable_states()
                items = ShareObjectRepository.list_shareable_items(
                    session, share, states, {'pageSize': 1000, 'isShared': True}
                ) #TODO
                item_uris = [item.shareItemUri for item in items.get('nodes', [])]
                ShareItemService.verify_items_share_object(uri=share_uri, item_uris=item_uris)
        return True

    @staticmethod
    def list_shared_tables_by_env_dataset(dataset_uri: str, env_uri: str):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            return [
                {'tableUri': t.tableUri, 'GlueTableName': t.GlueTableName}
                for t in S3ShareObjectRepository.query_dataset_tables_shared_with_env(
                    session, env_uri, dataset_uri, context.username, context.groups
                )
            ]

    @staticmethod
    @ResourcePolicyService.has_resource_permission(CREDENTIALS_DATASET)
    def get_dataset_shared_assume_role_url(uri):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            dataset = DatasetRepository.get_dataset_by_uri(session, uri)

            if dataset.SamlAdminGroupName in context.groups:
                role_arn = dataset.IAMDatasetAdminRoleArn
                account_id = dataset.AwsAccountId
                region = dataset.region
            else:
                share = S3ShareObjectRepository.get_share_by_dataset_attributes(
                    session=session, dataset_uri=uri, dataset_owner=context.username
                )
                shared_environment = EnvironmentService.get_environment_by_uri(
                    session=session, uri=share.environmentUri
                )
                env_group = EnvironmentService.get_environment_group(
                    session=session, group_uri=share.principalId, environment_uri=share.environmentUri
                )
                role_arn = env_group.environmentIAMRoleArn
                account_id = shared_environment.AwsAccountId
                region = shared_environment.region

        pivot_session = SessionHelper.remote_session(account_id, region)
        aws_session = SessionHelper.get_session(base_session=pivot_session, role_arn=role_arn)
        url = SessionHelper.get_console_access_url(
            aws_session,
            region=dataset.region,
            bucket=dataset.S3BucketName,
        )
        return url

    @staticmethod
    @ResourcePolicyService.has_resource_permission(GET_SHARE_OBJECT)
    def get_s3_consumption_data(uri):
        with get_context().db_engine.scoped_session() as session:
            share = ShareObjectRepository.get_share_by_uri(session, uri)
            dataset = DatasetRepository.get_dataset_by_uri(session, share.datasetUri)
            if dataset:
                environment = EnvironmentService.get_environment_by_uri(session, share.environmentUri)
                S3AccessPointName = utils.slugify(
                    share.datasetUri + '-' + share.principalId,
                    max_length=50,
                    lowercase=True,
                    regex_pattern='[^a-zA-Z0-9-]',
                    separator='-',
                )
                # Check if the share was made with a Glue Database
                datasetGlueDatabase = S3ShareItemService.get_glue_database_for_share(
                    dataset.GlueDatabaseName, dataset.AwsAccountId, dataset.region
                )
                old_shared_db_name = f'{datasetGlueDatabase}_shared_{uri}'[:254]
                database = GlueClient(
                    account_id=environment.AwsAccountId, region=environment.region, database=old_shared_db_name
                ).get_glue_database()
                warn('old_shared_db_name will be deprecated in v2.6.0', DeprecationWarning, stacklevel=2)
                sharedGlueDatabase = old_shared_db_name if database else f'{datasetGlueDatabase}_shared'
                return {
                    's3AccessPointName': S3AccessPointName,
                    'sharedGlueDatabase': sharedGlueDatabase,
                    's3bucketName': dataset.S3BucketName,
                }
            return {
                's3AccessPointName': 'Not Created',
                'sharedGlueDatabase': 'Not Created',
                's3bucketName': 'Not Created',
            }

    @staticmethod
    def list_shared_databases_tables_with_env_group(environmentUri: str, groupUri: str):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            return S3ShareObjectRepository.query_shared_glue_databases(
                session=session, groups=context.groups, env_uri=environmentUri, group_uri=groupUri
            ).all()

    @staticmethod
    def resolve_shared_db_name(GlueDatabaseName: str, shareUri: str, targetEnvAwsAccountId: str, targetEnvRegion: str):
        old_shared_db_name = (GlueDatabaseName + '_shared_' + shareUri)[:254]
        database = GlueClient(
            account_id=targetEnvAwsAccountId, database=old_shared_db_name, region=targetEnvRegion
        ).get_glue_database()
        return old_shared_db_name if database else GlueDatabaseName + '_shared'
