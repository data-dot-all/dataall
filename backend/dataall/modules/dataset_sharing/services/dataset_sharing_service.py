from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyService
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.base.context import get_context
from dataall.base.aws.sts import SessionHelper
from dataall.modules.dataset_sharing.db.share_object_repositories import (
    ShareObjectRepository,
    ShareItemSM,
)
from dataall.modules.dataset_sharing.services.share_item_service import ShareItemService
from dataall.modules.datasets_base.db.dataset_repositories import DatasetRepository
from dataall.modules.datasets.services.dataset_permissions import (
    MANAGE_DATASETS,
    UPDATE_DATASET,
    CREDENTIALS_DATASET,
)

from dataall.modules.datasets_base.db.dataset_models import Dataset

import logging

log = logging.getLogger(__name__)


class DatasetSharingService:
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
                )
                item_uris = [item.shareItemUri for item in items.get('nodes', [])]
                ShareItemService.verify_items_share_object(uri=share_uri, item_uris=item_uris)
        return True

    @staticmethod
    def list_dataset_share_objects(dataset: Dataset, data: dict = None):
        with get_context().db_engine.scoped_session() as session:
            return ShareObjectRepository.paginated_dataset_shares(session=session, uri=dataset.datasetUri, data=data)

    @staticmethod
    def list_shared_tables_by_env_dataset(dataset_uri: str, env_uri: str):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            return [
                {'tableUri': t.tableUri, 'GlueTableName': t.GlueTableName}
                for t in ShareObjectRepository.query_dataset_tables_shared_with_env(
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
                share = ShareObjectRepository.get_share_by_dataset_attributes(
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
