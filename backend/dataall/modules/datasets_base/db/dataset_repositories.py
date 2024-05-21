import logging
from dataall.core.activity.db.activity_models import Activity
from dataall.modules.datasets_base.db.dataset_models import DatasetBase, DatasetLock

logger = logging.getLogger(__name__)


class DatasetBaseRepository:
    """DAO layer for GENERIC Datasets"""

    @staticmethod
    def create_dataset_lock(session, dataset: DatasetBase):
        dataset_lock = DatasetLock(datasetUri=dataset.datasetUri, isLocked=False, acquiredBy='')
        session.add(dataset_lock)
        session.commit()

    @staticmethod
    def delete_dataset_lock(session, dataset: DatasetBase):
        dataset_lock = session.query(DatasetLock).filter(DatasetLock.datasetUri == dataset.datasetUri).first()
        session.delete(dataset_lock)
        session.commit()

    @staticmethod
    def update_dataset_activity(session, dataset: DatasetBase, username):
        activity = Activity(
            action='dataset:update',
            label='dataset:update',
            owner=username,
            summary=f'{username} updated dataset {dataset.name}',
            targetUri=dataset.datasetUri,
            targetType='dataset',
        )
        session.add(activity)
        session.commit()
