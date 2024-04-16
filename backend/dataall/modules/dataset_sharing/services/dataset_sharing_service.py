from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyService
from dataall.base.context import get_context
from dataall.base.db import exceptions
from dataall.modules.dataset_sharing.db.share_object_repositories import (
    ShareObjectRepository,
    ShareItemSM,
)
from dataall.modules.dataset_sharing.services.share_item_service import ShareItemService
from dataall.modules.datasets.services.dataset_permissions import (
    MANAGE_DATASETS,
    UPDATE_DATASET,
    DELETE_DATASET,
    DELETE_DATASET_TABLE,
    DELETE_DATASET_FOLDER,
)

from dataall.modules.datasets.services.dataset_service import DatasetServiceInterface
from dataall.modules.datasets.services.datasets_base_enums import DatasetRole

import logging

log = logging.getLogger(__name__)


class DatasetSharingService(DatasetServiceInterface):

    @staticmethod
    def append_to_list_user_datasets(session, username, groups):
        """Implemented as part of the DatasetServiceInterface"""
        return ShareObjectRepository.query_user_shared_datasets(session, username, groups)

    @staticmethod
    def check_before_delete(session, uri, **kwargs):
        """Implemented as part of the DatasetServiceInterface"""
        action = kwargs.get('action')
        if action in [DELETE_DATASET_FOLDER, DELETE_DATASET_TABLE]:
            has_share = ShareObjectRepository.has_shared_items(session, uri)
            if has_share:
                raise exceptions.ResourceShared(
                    action=action,
                    message='Revoke all shares for this item before deletion',
                )
        elif action in [DELETE_DATASET]:
            shares = ShareObjectRepository.list_dataset_shares_with_existing_shared_items(
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
            ShareObjectRepository.delete_shares(session, uri)
        elif action in [DELETE_DATASET]:
            ShareObjectRepository.delete_shares_with_no_shared_items(session, uri)
        else:
            raise exceptions.RequiredParameter('Delete action')
        return True

    @staticmethod
    def resolve_additional_dataset_user_role(session, uri, username, groups):
        """Implemented as part of the DatasetServiceInterface"""
        share = ShareObjectRepository.get_share_by_dataset_attributes(session, uri, username, groups)
        if share is not None:
            return DatasetRole.Shared.value
        return None


    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_DATASETS)
    @ResourcePolicyService.has_resource_permission(UPDATE_DATASET)
    def verify_dataset_share_objects(uri: str, share_uris: list):
        #TODO: when we abstract dataset_sharing_base from s3_dataset_sharing this function won't pollute the ShareObject service
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
