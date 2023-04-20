from dataall.db import exceptions
from dataall.db.models import Dataset


class DatasetRepository:
    """DAO layer for Datasets"""

    @staticmethod
    def get_dataset_by_uri(session, dataset_uri) -> Dataset:
        dataset: Dataset = session.query(Dataset).get(dataset_uri)
        if not dataset:
            raise exceptions.ObjectNotFound('Dataset', dataset_uri)
        return dataset
