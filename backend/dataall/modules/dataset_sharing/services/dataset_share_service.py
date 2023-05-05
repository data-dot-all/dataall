import logging
import re

from sqlalchemy import or_, case, func
from sqlalchemy.sql import and_

from dataall.api.constants import ShareableType, PrincipalType
from dataall.db import models, permissions
from dataall.db.api import has_resource_perm
from dataall.db.paginator import paginate
from dataall.modules.dataset_sharing.db.models import ShareObjectItem, ShareObject
from dataall.modules.dataset_sharing.services.share_object import ShareItemSM
from dataall.modules.datasets.db.models import DatasetStorageLocation, DatasetTable, Dataset


class DatasetShareService:

    @staticmethod
    @has_resource_perm(permissions.LIST_ENVIRONMENT_SHARED_WITH_OBJECTS)
    def paginated_shared_with_environment_datasets(
            session, username, groups, uri, data=None, check_perm=None
    ) -> dict:
        share_item_shared_states = ShareItemSM.get_share_item_shared_states()
        q = (
            session.query(
                ShareObjectItem.shareUri.label('shareUri'),
                Dataset.datasetUri.label('datasetUri'),
                Dataset.name.label('datasetName'),
                Dataset.description.label('datasetDescription'),
                models.Environment.environmentUri.label('environmentUri'),
                models.Environment.name.label('environmentName'),
                ShareObject.created.label('created'),
                ShareObject.principalId.label('principalId'),
                ShareObject.principalType.label('principalType'),
                ShareObjectItem.itemType.label('itemType'),
                ShareObjectItem.GlueDatabaseName.label('GlueDatabaseName'),
                ShareObjectItem.GlueTableName.label('GlueTableName'),
                ShareObjectItem.S3AccessPointName.label('S3AccessPointName'),
                models.Organization.organizationUri.label('organizationUri'),
                models.Organization.name.label('organizationName'),
                case(
                    [
                        (
                            ShareObjectItem.itemType
                            == ShareableType.Table.value,
                            func.concat(
                                DatasetTable.GlueDatabaseName,
                                '.',
                                DatasetTable.GlueTableName,
                            ),
                        ),
                        (
                            ShareObjectItem.itemType
                            == ShareableType.StorageLocation.value,
                            func.concat(DatasetStorageLocation.name),
                        ),
                    ],
                    else_='XXX XXXX',
                ).label('itemAccess'),
            )
            .join(
                ShareObject,
                ShareObject.shareUri == ShareObjectItem.shareUri,
            )
            .join(
                Dataset,
                ShareObject.datasetUri == Dataset.datasetUri,
            )
            .join(
                models.Environment,
                models.Environment.environmentUri == Dataset.environmentUri,
            )
            .join(
                models.Organization,
                models.Organization.organizationUri
                == models.Environment.organizationUri,
            )
            .outerjoin(
                DatasetTable,
                ShareObjectItem.itemUri == DatasetTable.tableUri,
            )
            .outerjoin(
                DatasetStorageLocation,
                ShareObjectItem.itemUri
                == DatasetStorageLocation.locationUri,
            )
            .filter(
                and_(
                    ShareObjectItem.status.in_(share_item_shared_states),
                    ShareObject.environmentUri == uri,
                )
            )
        )

        if data.get('datasetUri'):
            datasetUri = data.get('datasetUri')
            q = q.filter(ShareObject.datasetUri == datasetUri)

        if data.get('itemTypes', None):
            itemTypes = data.get('itemTypes')
            q = q.filter(
                or_(*[ShareObjectItem.itemType == t for t in itemTypes])
            )

        if data.get("uniqueShares", False):
            q = q.filter(ShareObject.principalType != PrincipalType.ConsumptionRole.value)
            q = q.distinct(ShareObject.shareUri)

        if data.get('term'):
            term = data.get('term')
            q = q.filter(ShareObjectItem.itemName.ilike('%' + term + '%'))

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
                ShareObjectItem.shareUri.label('shareUri'),
                Dataset.datasetUri.label('datasetUri'),
                Dataset.name.label('datasetName'),
                Dataset.description.label('datasetDescription'),
                models.Environment.environmentUri.label('environmentUri'),
                models.Environment.name.label('environmentName'),
                ShareObject.created.label('created'),
                ShareObject.principalId.label('principalId'),
                ShareObjectItem.itemType.label('itemType'),
                ShareObjectItem.GlueDatabaseName.label('GlueDatabaseName'),
                ShareObjectItem.GlueTableName.label('GlueTableName'),
                ShareObjectItem.S3AccessPointName.label('S3AccessPointName'),
                models.Organization.organizationUri.label('organizationUri'),
                models.Organization.name.label('organizationName'),
                case(
                    [
                        (
                            ShareObjectItem.itemType
                            == ShareableType.Table.value,
                            func.concat(
                                DatasetTable.GlueDatabaseName,
                                '.',
                                DatasetTable.GlueTableName,
                            ),
                        ),
                        (
                            ShareObjectItem.itemType
                            == ShareableType.StorageLocation.value,
                            func.concat(DatasetStorageLocation.name),
                        ),
                    ],
                    else_='XXX XXXX',
                ).label('itemAccess'),
            )
            .join(
                ShareObject,
                ShareObject.shareUri == ShareObjectItem.shareUri,
            )
            .join(
                Dataset,
                ShareObject.datasetUri == Dataset.datasetUri,
            )
            .join(
                models.Environment,
                models.Environment.environmentUri == Dataset.environmentUri,
            )
            .join(
                models.Organization,
                models.Organization.organizationUri
                == models.Environment.organizationUri,
            )
            .outerjoin(
                DatasetTable,
                ShareObjectItem.itemUri == DatasetTable.tableUri,
            )
            .outerjoin(
                DatasetStorageLocation,
                ShareObjectItem.itemUri
                == DatasetStorageLocation.locationUri,
            )
            .filter(
                and_(
                    ShareObjectItem.status.in_(share_item_shared_states),
                    ShareObject.environmentUri == envUri,
                    ShareObject.principalId == groupUri,
                )
            )
        )

        if data.get('datasetUri'):
            datasetUri = data.get('datasetUri')
            q = q.filter(ShareObject.datasetUri == datasetUri)

        if data.get('itemTypes', None):
            itemTypes = data.get('itemTypes')
            q = q.filter(
                or_(*[ShareObjectItem.itemType == t for t in itemTypes])
            )
        if data.get('term'):
            term = data.get('term')
            q = q.filter(ShareObjectItem.itemName.ilike('%' + term + '%'))

        return paginate(
            query=q, page=data.get('page', 1), page_size=data.get('pageSize', 10)
        ).to_dict()
