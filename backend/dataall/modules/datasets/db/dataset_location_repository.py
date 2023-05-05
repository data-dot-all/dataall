import logging

from sqlalchemy import and_, or_

from dataall.core.context import get_context
from dataall.core.permission_checker import has_tenant_permission, has_resource_permission
from dataall.db.api import Glossary
from dataall.db import paginate, exceptions
from dataall.modules.dataset_sharing.db.models import ShareObjectItem
from dataall.modules.dataset_sharing.services.share_object import ShareItemSM
from dataall.modules.datasets_base.db.dataset_repository import DatasetRepository
from dataall.modules.datasets_base.db.models import DatasetStorageLocation
from dataall.modules.datasets.services.permissions import MANAGE_DATASETS, LIST_DATASET_FOLDERS, CREATE_DATASET_FOLDER, \
    DELETE_DATASET_FOLDER, UPDATE_DATASET_FOLDER

logger = logging.getLogger(__name__)


class DatasetLocationRepository:
    @staticmethod
    @has_tenant_permission(MANAGE_DATASETS)
    @has_resource_permission(CREATE_DATASET_FOLDER)
    def create_dataset_location(
        session,
        uri: str,
        data: dict = None
    ) -> DatasetStorageLocation:
        dataset = DatasetRepository.get_dataset_by_uri(session, uri)
        exists = (
            session.query(DatasetStorageLocation)
            .filter(
                and_(
                    DatasetStorageLocation.datasetUri == dataset.datasetUri,
                    DatasetStorageLocation.S3Prefix == data['prefix'],
                )
            )
            .count()
        )

        if exists:
            raise exceptions.ResourceAlreadyExists(
                action='Create Folder',
                message=f'Folder: {data["prefix"]} already exist on dataset {uri}',
            )

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

        if 'terms' in data.keys():
            Glossary.set_glossary_terms_links(
                session,
                get_context().username,
                location.locationUri,
                'DatasetStorageLocation',
                data.get('terms', []),
            )

        return location

    @staticmethod
    @has_tenant_permission(MANAGE_DATASETS)
    @has_resource_permission(LIST_DATASET_FOLDERS)
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
    @has_tenant_permission(MANAGE_DATASETS)
    @has_resource_permission(LIST_DATASET_FOLDERS)
    def get_dataset_location(
        session,
        uri: str,
        data: dict = None,
    ) -> DatasetStorageLocation:
        return DatasetLocationRepository.get_location_by_uri(session, data['locationUri'])

    @staticmethod
    @has_tenant_permission(MANAGE_DATASETS)
    @has_resource_permission(UPDATE_DATASET_FOLDER)
    def update_dataset_location(
        session,
        uri: str,
        data: dict = None,
    ) -> DatasetStorageLocation:

        location = data.get(
            'location',
            DatasetLocationRepository.get_location_by_uri(session, data['locationUri']),
        )

        for k in data.keys():
            setattr(location, k, data.get(k))

        if 'terms' in data.keys():
            Glossary.set_glossary_terms_links(
                session,
                get_context().username,
                location.locationUri,
                'DatasetStorageLocation',
                data.get('terms', []),
            )
        return location

    @staticmethod
    @has_tenant_permission(MANAGE_DATASETS)
    @has_resource_permission(DELETE_DATASET_FOLDER)
    def delete_dataset_location(
        session,
        uri: str,
        data: dict = None,
    ):
        location = DatasetLocationRepository.get_location_by_uri(
            session, data['locationUri']
        )
        share_item_shared_states = ShareItemSM.get_share_item_shared_states()
        share_item = (
            session.query(ShareObjectItem)
            .filter(
                and_(
                    ShareObjectItem.itemUri == location.locationUri,
                    ShareObjectItem.status.in_(share_item_shared_states)
                )
            )
            .first()
        )
        if share_item:
            raise exceptions.ResourceShared(
                action=DELETE_DATASET_FOLDER,
                message='Revoke all folder shares before deletion',
            )
        session.query(ShareObjectItem).filter(
            ShareObjectItem.itemUri == location.locationUri,
        ).delete()

        session.delete(location)
        Glossary.delete_glossary_terms_links(
            session,
            target_uri=location.locationUri,
            target_type='DatasetStorageLocation',
        )
        return True

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
            .filter(
                and_(
                    DatasetStorageLocation.datasetUri == dataset_uri,
                )
            )
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
    def paginated_dataset_locations(
            session, username, groups, uri, data=None, check_perm=None
    ) -> dict:
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

