import logging

from dataall.modules.datasets_base.db.dataset_models import DatasetBucket, Dataset

logger = logging.getLogger(__name__)


class DatasetBucketRepository:

    @staticmethod
    def create_dataset_bucket(
        session,
        dataset: Dataset,
        data: dict = None
    ) -> DatasetBucket:
        bucket = DatasetBucket(
            datasetUri=dataset.datasetUri,
            label=data.get('label'),
            description=data.get('description', 'No description provided'),
            tags=data.get('tags', []),
            S3BucketName=dataset.S3BucketName,
            AwsAccountId=dataset.AwsAccountId,
            owner=dataset.owner,
            region=dataset.region,
            KmsAlias=dataset.KmsAlias,
            imported=dataset.imported,
            importedKmsKey=dataset.importedKmsKey,
        )
        session.add(bucket)
        session.commit()
        return bucket

    @staticmethod
    def delete_dataset_buckets(session, dataset_uri) -> bool:
        buckets = (
            session.query(DatasetBucket)
            .filter(DatasetBucket.datasetUri == dataset_uri)
            .all()
        )
        for bucket in buckets:
            session.delete(bucket)
