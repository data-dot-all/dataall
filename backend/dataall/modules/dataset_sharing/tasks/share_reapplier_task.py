import logging
import os
import sys
from dataall.modules.dataset_sharing.api.types import ShareObject
from dataall.modules.dataset_sharing.db.share_object_repositories import ShareObjectRepository
from dataall.modules.dataset_sharing.services.dataset_sharing_enums import ShareItemHealthStatus
from dataall.modules.dataset_sharing.services.data_sharing_service import DataSharingService
from dataall.base.db import get_engine

root = logging.getLogger()
root.setLevel(logging.INFO)
if not root.hasHandlers():
    root.addHandler(logging.StreamHandler(sys.stdout))
log = logging.getLogger(__name__)


def verify_shares(engine):
    """
    A method used by the scheduled ECS Task to re-apply_share() on all data.all active shares
    """
    with engine.scoped_session() as session:
        processed_share_objects = []
        all_share_objects: [ShareObject] = ShareObjectRepository.list_all_active_share_objects(session)
        log.info(f'Found {len(all_share_objects)} share objects ')
        share_object: ShareObject
        for share_object in all_share_objects:
            log.info(
                f'Re-applying Share Items for Share Object with Requestor: {share_object.principalId} on Target Dataset: {share_object.datasetUri}'
            )
            processed_share_objects.append(share_object.shareUri)
            ShareObjectRepository.update_share_item_health_status_batch(
                session=session,
                share_uri=share_object.shareUri,
                old_status=ShareItemHealthStatus.Unhealthy.value,
                new_status=ShareItemHealthStatus.PendingReApply.value,
            )
            DataSharingService.reapply_share(engine, share_uri=share_object.shareUri)
        return processed_share_objects


if __name__ == '__main__':
    ENVNAME = os.environ.get('envname', 'local')
    ENGINE = get_engine(envname=ENVNAME)
    verify_shares(engine=ENGINE)
