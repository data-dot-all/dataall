import logging
import os
import sys

from dataall.modules.shares_base.db.share_object_repositories import ShareObjectRepository
from dataall.modules.shares_base.db.share_object_models import ShareObject
from dataall.modules.shares_base.db.share_state_machines_repositories import ShareStatusRepository
from dataall.modules.shares_base.services.shares_enums import ShareItemHealthStatus
from dataall.modules.shares_base.services.sharing_service import SharingService
from dataall.base.db import get_engine

from dataall.base.loader import load_modules, ImportMode

log = logging.getLogger(__name__)


class EcsBulkShareRepplyService:
    @classmethod
    def process_reapply_shares_for_dataset(cls, engine, dataset_uri):
        with engine.scoped_session() as session:
            processed_share_objects = []
            share_objects_for_dataset = ShareObjectRepository.list_active_share_object_for_dataset(
                session=session, dataset_uri=dataset_uri
            )
            log.info(f'Found {len(share_objects_for_dataset)} active share objects on dataset with uri: {dataset_uri}')
            share_object: ShareObject
            for share_object in share_objects_for_dataset:
                log.info(
                    f'Re-applying Share Items for Share Object (Share URI: {share_object.shareUri} ) with Requestor: {share_object.principalId} on Target Dataset: {share_object.datasetUri}'
                )
                processed_share_objects.append(share_object.shareUri)
                ShareStatusRepository.update_share_item_health_status_batch(
                    session=session,
                    share_uri=share_object.shareUri,
                    old_status=ShareItemHealthStatus.Unhealthy.value,
                    new_status=ShareItemHealthStatus.PendingReApply.value,
                )
                SharingService.reapply_share(engine, share_uri=share_object.shareUri)
            return processed_share_objects

    @classmethod
    def process_reapply_shares(cls, engine):
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
                ShareStatusRepository.update_share_item_health_status_batch(
                    session=session,
                    share_uri=share_object.shareUri,
                    old_status=ShareItemHealthStatus.Unhealthy.value,
                    new_status=ShareItemHealthStatus.PendingReApply.value,
                )
                SharingService.reapply_share(engine, share_uri=share_object.shareUri)
            return processed_share_objects


def reapply_shares(engine, dataset_uri):
    """
    A method used by the scheduled ECS Task to re-apply_share() on all data.all active shares
    If dataset_uri is provided this ECS will reapply on all unhealthy shares belonging to a dataset
    else it will reapply on all data.all active unhealthy shares.
    """
    if dataset_uri:
        return EcsBulkShareRepplyService.process_reapply_shares_for_dataset(engine, dataset_uri)
    else:
        return EcsBulkShareRepplyService.process_reapply_shares(engine)


if __name__ == '__main__':
    load_modules(modes={ImportMode.SHARES_TASK})
    ENVNAME = os.environ.get('envname', 'local')
    ENGINE = get_engine(envname=ENVNAME)
    dataset_uri = os.environ.get('datasetUri', '')
    processed_shares = reapply_shares(engine=ENGINE, dataset_uri=dataset_uri)
    log.info(f'Finished processing {len(processed_shares)} shares')
