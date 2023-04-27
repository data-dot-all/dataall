from operator import and_

from dataall.db import exceptions
from dataall.modules.datasets.db.models import Dataset


class DatasetRepository:
    """DAO layer for Datasets"""

    @staticmethod
    def get_dataset_by_uri(session, dataset_uri) -> Dataset:
        dataset: Dataset = session.query(Dataset).get(dataset_uri)
        if not dataset:
            raise exceptions.ObjectNotFound('Dataset', dataset_uri)
        return dataset

    @staticmethod
    def count_group_datasets(session, environment_uri, group_uri) -> int:
        return (
            session.query(Dataset)
            .filter(
                and_(
                    Dataset.environmentUri == environment_uri,
                    Dataset.SamlAdminGroupName == group_uri
                ))
            .count()
        )

