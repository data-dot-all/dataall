import logging
from typing import List

from sqlalchemy import and_, or_

from . import has_tenant_perm, has_resource_perm, Glossary
from .. import models, api, paginate, permissions, exceptions
from .dataset import Dataset

logger = logging.getLogger(__name__)


class DatasetStorageLocation:
    @staticmethod
    @has_tenant_perm(permissions.MANAGE_DATASETS)
    @has_resource_perm(permissions.CREATE_DATASET_FOLDER)
    def create_dataset_location(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ) -> models.DatasetStorageLocation:
        dataset = Dataset.get_dataset_by_uri(session, uri)
        exists = (
            session.query(models.DatasetStorageLocation)
            .filter(
                and_(
                    models.DatasetStorageLocation.datasetUri == dataset.datasetUri,
                    models.DatasetStorageLocation.S3Prefix == data['prefix'],
                )
            )
            .count()
        )

        if exists:
            raise exceptions.ResourceAlreadyExists(
                action='Create Folder',
                message=f'Folder: {data["prefix"]} already exist on dataset {uri}',
            )

        location = models.DatasetStorageLocation(
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
    @has_tenant_perm(permissions.MANAGE_DATASETS)
    @has_resource_perm(permissions.LIST_DATASET_FOLDERS)
    def list_dataset_locations(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ) -> dict:
        query = (
            session.query(models.DatasetStorageLocation)
            .filter(models.DatasetStorageLocation.datasetUri == uri)
            .order_by(models.DatasetStorageLocation.created.desc())
        )
        if data.get('term'):
            term = data.get('term')
            query = query.filter(
                models.DatasetStorageLocation.label.ilike('%' + term + '%')
            )
        return paginate(
            query, page=data.get('page', 1), page_size=data.get('pageSize', 10)
        ).to_dict()

    @staticmethod
    @has_tenant_perm(permissions.MANAGE_DATASETS)
    @has_resource_perm(permissions.LIST_DATASET_FOLDERS)
    def get_dataset_location(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ) -> models.DatasetStorageLocation:
        return DatasetStorageLocation.get_location_by_uri(session, data['locationUri'])

    @staticmethod
    @has_tenant_perm(permissions.MANAGE_DATASETS)
    @has_resource_perm(permissions.UPDATE_DATASET_FOLDER)
    def update_dataset_location(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ) -> models.DatasetStorageLocation:

        location = data.get(
            'location',
            DatasetStorageLocation.get_location_by_uri(session, data['locationUri']),
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
    @has_tenant_perm(permissions.MANAGE_DATASETS)
    @has_resource_perm(permissions.DELETE_DATASET_FOLDER)
    def delete_dataset_location(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ):
        location = DatasetStorageLocation.get_location_by_uri(
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
                action=permissions.DELETE_DATASET_FOLDER,
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
    def get_location_by_uri(session, location_uri) -> models.DatasetStorageLocation:
        location: DatasetStorageLocation = session.query(
            models.DatasetStorageLocation
        ).get(location_uri)
        if not location:
            raise exceptions.ObjectNotFound('Folder', location_uri)
        return location

    @staticmethod
    def get_location_by_s3_prefix(session, s3_prefix, accountid, region):
        location: models.DatasetStorageLocation = (
            session.query(models.DatasetStorageLocation)
            .filter(
                and_(
                    models.DatasetStorageLocation.S3Prefix.startswith(s3_prefix),
                    models.DatasetStorageLocation.AWSAccountId == accountid,
                    models.DatasetStorageLocation.region == region,
                )
            )
            .first()
        )
        if not location:
            logging.info(f'No location found for  {s3_prefix}|{accountid}|{region}')
        else:
            logging.info(f'Found location {location.locationUri}|{location.S3Prefix}')
            return location
