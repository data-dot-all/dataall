import logging

from sqlalchemy import and_, or_

from dataall.core.context import get_context
from dataall.db.api import Glossary
from dataall.db import paginate, exceptions
from dataall.modules.dataset_sharing.db.models import ShareObjectItem
from dataall.modules.dataset_sharing.db.share_object_repository import ShareItemSM
from dataall.modules.datasets_base.db.dataset_repository import DatasetRepository
from dataall.modules.datasets_base.db.models import DatasetStorageLocation, Dataset
from dataall.modules.datasets.services.dataset_permissions import DELETE_DATASET_FOLDER

logger = logging.getLogger(__name__)


class DatasetLocationRepository:

    @staticmethod
    def exists(session, dataset_uri: str, prefix: str):
        return (
            session.query(DatasetStorageLocation)
            .filter(
                and_(
                    DatasetStorageLocation.datasetUri == dataset_uri,
                    DatasetStorageLocation.S3Prefix == prefix,
                )
            )
            .count()
        )

    @staticmethod
    def create_dataset_location(
        session,
        dataset: Dataset,
        data: dict = None
    ) -> DatasetStorageLocation:
        location = DatasetStorageLocation(
            datasetUri=dataset.datasetUri,
            label=data.get('label'),
            description=data.get('description', 'No description provided'),
            tags=data.get('tags', []),
            S3Prefix=data.get('prefix'),
            S3BucketName=dataset.S3BucketName,
            AWSAccountId=dataset.AwsAccountId,
            owner=dataset.owner,
            region=dataset.region,
        )
        session.add(location)
        session.commit()
        return location

    @staticmethod
    def list_dataset_locations(
        session,
        uri: str,
        data: dict = None,
    ) -> dict:
        query = (
            session.query(DatasetStorageLocation)
            .filter(DatasetStorageLocation.datasetUri == uri)
            .order_by(DatasetStorageLocation.created.desc())
        )
        if data.get('term'):
            term = data.get('term')
            query = query.filter(
                DatasetStorageLocation.label.ilike('%' + term + '%')
            )
        return paginate(
            query, page=data.get('page', 1), page_size=data.get('pageSize', 10)
        ).to_dict()

    @staticmethod
    def delete(session, location):
        session.delete(location)

    @staticmethod
    def get_location_by_uri(session, location_uri) -> DatasetStorageLocation:
        location: DatasetStorageLocation = session.query(
            DatasetStorageLocation
        ).get(location_uri)
        if not location:
            raise exceptions.ObjectNotFound('Folder', location_uri)
        return location

    @staticmethod
    def get_location_by_s3_prefix(session, s3_prefix, accountid, region):
        location: DatasetStorageLocation = (
            session.query(DatasetStorageLocation)
            .filter(
                and_(
                    DatasetStorageLocation.S3Prefix.startswith(s3_prefix),
                    DatasetStorageLocation.AWSAccountId == accountid,
                    DatasetStorageLocation.region == region,
                )
            )
            .first()
        )
        if not location:
            logging.info(f'No location found for  {s3_prefix}|{accountid}|{region}')
        else:
            logging.info(f'Found location {location.locationUri}|{location.S3Prefix}')
            return location

    @staticmethod
    def count_dataset_locations(session, dataset_uri):
        return (
            session.query(DatasetStorageLocation)
            .filter(DatasetStorageLocation.datasetUri == dataset_uri)
            .count()
        )

    @staticmethod
    def delete_dataset_locations(session, dataset_uri) -> bool:
        locations = (
            session.query(DatasetStorageLocation)
            .filter(DatasetStorageLocation.datasetUri == dataset_uri)
            .all()
        )
        for location in locations:
            session.delete(location)
        return True

    @staticmethod
    def get_dataset_folders(session, dataset_uri):
        """return the dataset folders"""
        return (
            session.query(DatasetStorageLocation)
            .filter(DatasetStorageLocation.datasetUri == dataset_uri)
            .all()
        )

    @staticmethod
    def paginated_dataset_locations(session, uri, data=None) -> dict:
        query = session.query(DatasetStorageLocation).filter(
            DatasetStorageLocation.datasetUri == uri
        )
        if data and data.get('term'):
            query = query.filter(
                or_(
                    *[
                        DatasetStorageLocation.name.ilike(
                            '%' + data.get('term') + '%'
                        ),
                        DatasetStorageLocation.S3Prefix.ilike(
                            '%' + data.get('term') + '%'
                        ),
                    ]
                )
            )
        return paginate(
            query=query, page_size=data.get('pageSize', 10), page=data.get('page', 1)
        ).to_dict()
