import logging

from sqlalchemy import and_, or_

from dataall.db.api import has_tenant_perm, has_resource_perm, Glossary
from dataall.db import models, api, paginate, exceptions
from dataall.modules.datasets.db.dataset_repository import DatasetRepository
from dataall.modules.datasets.db.models import DatasetStorageLocation
from dataall.modules.datasets.services.permissions import MANAGE_DATASETS, LIST_DATASET_FOLDERS, CREATE_DATASET_FOLDER, \
    DELETE_DATASET_FOLDER, UPDATE_DATASET_FOLDER

logger = logging.getLogger(__name__)


class DatasetLocationService:
    @staticmethod
    @has_tenant_perm(MANAGE_DATASETS)
    @has_resource_perm(CREATE_DATASET_FOLDER)
    def create_dataset_location(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
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
                username,
                location.locationUri,
                'DatasetStorageLocation',
                data.get('terms', []),
            )

        return location

    @staticmethod
    @has_tenant_perm(MANAGE_DATASETS)
    @has_resource_perm(LIST_DATASET_FOLDERS)
    def list_dataset_locations(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
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
    @has_tenant_perm(MANAGE_DATASETS)
    @has_resource_perm(LIST_DATASET_FOLDERS)
    def get_dataset_location(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ) -> DatasetStorageLocation:
        return DatasetLocationService.get_location_by_uri(session, data['locationUri'])

    @staticmethod
    @has_tenant_perm(MANAGE_DATASETS)
    @has_resource_perm(UPDATE_DATASET_FOLDER)
    def update_dataset_location(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ) -> DatasetStorageLocation:

        location = data.get(
            'location',
            DatasetLocationService.get_location_by_uri(session, data['locationUri']),
        )

        for k in data.keys():
            setattr(location, k, data.get(k))

        if 'terms' in data.keys():
            Glossary.set_glossary_terms_links(
                session,
                username,
                location.locationUri,
                'DatasetStorageLocation',
                data.get('terms', []),
            )
        return location

    @staticmethod
    @has_tenant_perm(MANAGE_DATASETS)
    @has_resource_perm(DELETE_DATASET_FOLDER)
    def delete_dataset_location(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ):
        location = DatasetLocationService.get_location_by_uri(
            session, data['locationUri']
        )
        share_item_shared_states = api.ShareItemSM.get_share_item_shared_states()
        share_item = (
            session.query(models.ShareObjectItem)
            .filter(
                and_(
                    models.ShareObjectItem.itemUri == location.locationUri,
                    models.ShareObjectItem.status.in_(share_item_shared_states)
                )
            )
            .first()
        )
        if share_item:
            raise exceptions.ResourceShared(
                action=DELETE_DATASET_FOLDER,
                message='Revoke all folder shares before deletion',
            )
        session.query(models.ShareObjectItem).filter(
            models.ShareObjectItem.itemUri == location.locationUri,
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

