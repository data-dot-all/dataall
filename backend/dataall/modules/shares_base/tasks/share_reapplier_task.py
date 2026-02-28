import logging
import os
import sys
from typing import List

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
    def reapply_for_share_objects(cls, engine, session, share_objects: List[str]):
        share_object: ShareObject
        processed_shares = []
        for share_object in share_objects:
            log.info(
                f'Re-applying Share Items for Share Object (Share URI: {share_object.shareUri} ) with Requestor: {share_object.principalId} on Target Dataset: {share_object.datasetUri}'
            )
            processed_shares.append(share_object)
            ShareStatusRepository.update_share_item_health_status_batch(
                session=session,
                share_uri=share_object.shareUri,
                old_status=ShareItemHealthStatus.Unhealthy.value,
                new_status=ShareItemHealthStatus.PendingReApply.value,
            )
            SharingService.reapply_share(engine, share_uri=share_object.shareUri)
        return processed_shares

    @classmethod
    def process_reapply_shares_for_dataset(cls, engine, dataset_uris: List[str]):
        with engine.scoped_session() as session:
            processed_share_objects = []
            log.info(f'Found {len(dataset_uris)} datasets for which shares have to be reapplied')
            for dataset_uri in dataset_uris:
                share_objects_for_dataset = ShareObjectRepository.list_active_share_object_for_dataset(
                    session=session, dataset_uri=dataset_uri
                )
                log.info(
                    f'Found {len(share_objects_for_dataset)} active share objects on dataset with uri: {dataset_uri}'
                )
                processed_shares = cls.reapply_for_share_objects(
                    engine, session, share_objects=share_objects_for_dataset
                )
                processed_share_objects.extend(processed_shares)
            return processed_share_objects

    @classmethod
    def process_reapply_shares(cls, engine):
        with engine.scoped_session() as session:
            processed_share_objects = []
            all_share_objects: [ShareObject] = ShareObjectRepository.list_all_active_share_objects(session)
            log.info(f'Found {len(all_share_objects)} share objects for reapply')
            processed_shares = cls.reapply_for_share_objects(engine, session, share_objects=all_share_objects)
            processed_share_objects.extend(processed_shares)
            return processed_share_objects

    @classmethod
    def process_reapply_shares_for_share_uris(cls, engine, share_object_uris: List[str]):
        with engine.scoped_session() as session:
            share_objects: List[ShareObject] = [
                ShareObjectRepository.get_share_by_uri(session, share_uri) for share_uri in share_object_uris
            ]
            processed_share_objects = []
            log.info(f'{len(share_objects)} share objects to be reapplied')
            processed_shares = cls.reapply_for_share_objects(engine, session, share_objects=share_objects)
            processed_share_objects.extend(processed_shares)
            return processed_share_objects


def reapply_shares(engine, dataset_uris: List[str], share_object_uris: List[str]):
    """
    A method used by the scheduled ECS Task to re-apply_share() on all data.all active shares
    If dataset_uri is provided this ECS will reapply on all unhealthy shares belonging to a dataset
    else it will reapply on all data.all active unhealthy shares.
    """
    processed_shares = []
    if len(dataset_uris) > 0:
        processed_shares.append(EcsBulkShareRepplyService.process_reapply_shares_for_dataset(engine, dataset_uris))
    if len(share_object_uris) > 0:
        processed_shares.append(
            EcsBulkShareRepplyService.process_reapply_shares_for_share_uris(engine, share_object_uris)
        )
    else:
        processed_shares.append(EcsBulkShareRepplyService.process_reapply_shares(engine))

    return processed_shares


if __name__ == '__main__':
    load_modules(modes={ImportMode.SHARES_TASK})
    ENVNAME = os.environ.get('envname', 'local')
    ENGINE = get_engine(envname=ENVNAME)
    dataset_uris: List[str] = os.environ.get('datasetUris', [])
    share_object_uris: List[str] = os.environ.get('shareUris', [])
    processed_shares = reapply_shares(engine=ENGINE, dataset_uris=dataset_uris, share_object_uris=share_object_uris)
    log.info(f'Finished processing {len(processed_shares)} shares')
