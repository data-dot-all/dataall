from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyService
from dataall.base.context import get_context
from dataall.modules.dataset_sharing.db.share_object_repositories import (
    ShareObjectRepository,
    ShareItemSM,
)
from dataall.modules.dataset_sharing.services.share_item_service import ShareItemService
from dataall.modules.datasets.services.dataset_permissions import (
    MANAGE_DATASETS,
    UPDATE_DATASET,
)

import logging

log = logging.getLogger(__name__)


class DatasetSharingService:

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
