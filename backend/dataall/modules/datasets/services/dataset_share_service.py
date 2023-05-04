import logging
import re

from sqlalchemy import or_, case, func
from sqlalchemy.sql import and_

from dataall.api.constants import ShareableType
from dataall.db import models, permissions
from dataall.db.api import has_resource_perm, ShareItemSM
from dataall.db.paginator import paginate
from dataall.modules.datasets.db.models import DatasetStorageLocation, DatasetTable


class DatasetShareService:

    @staticmethod
    @has_resource_perm(permissions.LIST_ENVIRONMENT_SHARED_WITH_OBJECTS)
    def paginated_shared_with_environment_datasets(
            session, username, groups, uri, data=None, check_perm=None
    ) -> dict:
        share_item_shared_states = ShareItemSM.get_share_item_shared_states()
        q = (
            session.query(
                models.ShareObjectItem.shareUri.label('shareUri'),
                models.Dataset.datasetUri.label('datasetUri'),
                models.Dataset.name.label('datasetName'),
                models.Dataset.description.label('datasetDescription'),
                models.Environment.environmentUri.label('environmentUri'),
                models.Environment.name.label('environmentName'),
                models.ShareObject.created.label('created'),
                models.ShareObject.principalId.label('principalId'),
                models.ShareObjectItem.itemType.label('itemType'),
                models.ShareObjectItem.GlueDatabaseName.label('GlueDatabaseName'),
                models.ShareObjectItem.GlueTableName.label('GlueTableName'),
                models.ShareObjectItem.S3AccessPointName.label('S3AccessPointName'),
                models.Organization.organizationUri.label('organizationUri'),
                models.Organization.name.label('organizationName'),
                case(
                    [
                        (
                            models.ShareObjectItem.itemType
                            == ShareableType.Table.value,
                            func.concat(
                                DatasetTable.GlueDatabaseName,
                                '.',
                                DatasetTable.GlueTableName,
                            ),
                        ),
                        (
                            models.ShareObjectItem.itemType
                            == ShareableType.StorageLocation.value,
                            func.concat(DatasetStorageLocation.name),
                        ),
                    ],
                    else_='XXX XXXX',
                ).label('itemAccess'),
            )
            .join(
                models.ShareObject,
                models.ShareObject.shareUri == models.ShareObjectItem.shareUri,
            )
            .join(
                models.Dataset,
                models.ShareObject.datasetUri == models.Dataset.datasetUri,
            )
            .join(
                models.Environment,
                models.Environment.environmentUri == models.Dataset.environmentUri,
            )
            .join(
                models.Organization,
                models.Organization.organizationUri
                == models.Environment.organizationUri,
            )
            .outerjoin(
                DatasetTable,
                models.ShareObjectItem.itemUri == DatasetTable.tableUri,
            )
            .outerjoin(
                DatasetStorageLocation,
                models.ShareObjectItem.itemUri
                == DatasetStorageLocation.locationUri,
            )
            .filter(
                and_(
                    models.ShareObjectItem.status.in_(share_item_shared_states),
                    models.ShareObject.environmentUri == uri,
                )
            )
        )

        if data.get('datasetUri'):
            datasetUri = data.get('datasetUri')
            q = q.filter(models.ShareObject.datasetUri == datasetUri)

        if data.get('itemTypes', None):
            itemTypes = data.get('itemTypes')
            q = q.filter(
                or_(*[models.ShareObjectItem.itemType == t for t in itemTypes])
            )

        if data.get("uniqueDatasets", False):
            q = q.distinct(models.ShareObject.datasetUri)

        if data.get('term'):
            term = data.get('term')
            q = q.filter(models.ShareObjectItem.itemName.ilike('%' + term + '%'))

        return paginate(
            query=q, page=data.get('page', 1), page_size=data.get('pageSize', 10)
        ).to_dict()

    @staticmethod
    def paginated_shared_with_environment_group_datasets(
            session, username, groups, envUri, groupUri, data=None, check_perm=None
    ) -> dict:
        share_item_shared_states = ShareItemSM.get_share_item_shared_states()
        q = (
            session.query(
                models.ShareObjectItem.shareUri.label('shareUri'),
                models.Dataset.datasetUri.label('datasetUri'),
                models.Dataset.name.label('datasetName'),
                models.Dataset.description.label('datasetDescription'),
                models.Environment.environmentUri.label('environmentUri'),
                models.Environment.name.label('environmentName'),
                models.ShareObject.created.label('created'),
                models.ShareObject.principalId.label('principalId'),
                models.ShareObjectItem.itemType.label('itemType'),
                models.ShareObjectItem.GlueDatabaseName.label('GlueDatabaseName'),
                models.ShareObjectItem.GlueTableName.label('GlueTableName'),
                models.ShareObjectItem.S3AccessPointName.label('S3AccessPointName'),
                models.Organization.organizationUri.label('organizationUri'),
                models.Organization.name.label('organizationName'),
                case(
                    [
                        (
                            models.ShareObjectItem.itemType
                            == ShareableType.Table.value,
                            func.concat(
                                DatasetTable.GlueDatabaseName,
                                '.',
                                DatasetTable.GlueTableName,
                            ),
                        ),
                        (
                            models.ShareObjectItem.itemType
                            == ShareableType.StorageLocation.value,
                            func.concat(DatasetStorageLocation.name),
                        ),
                    ],
                    else_='XXX XXXX',
                ).label('itemAccess'),
            )
            .join(
                models.ShareObject,
                models.ShareObject.shareUri == models.ShareObjectItem.shareUri,
            )
            .join(
                models.Dataset,
                models.ShareObject.datasetUri == models.Dataset.datasetUri,
            )
            .join(
                models.Environment,
                models.Environment.environmentUri == models.Dataset.environmentUri,
            )
            .join(
                models.Organization,
                models.Organization.organizationUri
                == models.Environment.organizationUri,
            )
            .outerjoin(
                DatasetTable,
                models.ShareObjectItem.itemUri == DatasetTable.tableUri,
            )
            .outerjoin(
                DatasetStorageLocation,
                models.ShareObjectItem.itemUri
                == DatasetStorageLocation.locationUri,
            )
            .filter(
                and_(
                    models.ShareObjectItem.status.in_(share_item_shared_states),
                    models.ShareObject.environmentUri == envUri,
                    models.ShareObject.principalId == groupUri,
                )
            )
        )

        if data.get('datasetUri'):
            datasetUri = data.get('datasetUri')
            q = q.filter(models.ShareObject.datasetUri == datasetUri)

        if data.get('itemTypes', None):
            itemTypes = data.get('itemTypes')
            q = q.filter(
                or_(*[models.ShareObjectItem.itemType == t for t in itemTypes])
            )
        if data.get('term'):
            term = data.get('term')
            q = q.filter(models.ShareObjectItem.itemName.ilike('%' + term + '%'))

        return paginate(
            query=q, page=data.get('page', 1), page_size=data.get('pageSize', 10)
        ).to_dict()
