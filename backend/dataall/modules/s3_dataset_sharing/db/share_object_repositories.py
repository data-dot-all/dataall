import logging
from warnings import warn
from typing import List
from datetime import datetime

from sqlalchemy import and_, or_, func, case
from sqlalchemy.orm import Query

from dataall.core.environment.db.environment_models import Environment, EnvironmentGroup
from dataall.core.organizations.db.organization_models import Organization
from dataall.base.db import exceptions, paginate
from dataall.modules.dataset_sharing_base.services.dataset_sharing_base_enums import (
    ShareItemHealthStatus,
    ShareObjectActions,
    ShareObjectStatus,
    ShareItemActions,
    ShareItemStatus,
    ShareableType,
    PrincipalType,
)
from dataall.modules.dataset_sharing_base.db.share_object_base_models import ShareObjectItem, ShareObject
from dataall.modules.dataset_sharing_base.db.share_object_base_repositories import ShareObjectBaseRepository, ShareItemSM
from dataall.modules.s3_datasets.db.dataset_repositories import S3DatasetRepository
from dataall.modules.datasets_base.db.dataset_base_models import Dataset
from dataall.modules.s3_datasets.db.dataset_models import DatasetStorageLocation, DatasetTable, S3Dataset, DatasetBucket

logger = logging.getLogger(__name__)



class S3ShareObjectRepository:
    #TODO: review the split between base repository and S3 repository

    @staticmethod
    def get_share_item(session, item_type, item_uri):
        if item_type == ShareableType.Table.value:
            return session.query(DatasetTable).get(item_uri)
        if item_type == ShareableType.StorageLocation.value:
            return session.query(DatasetStorageLocation).get(item_uri)
        if item_type == ShareableType.S3Bucket.value:
            return session.query(DatasetBucket).get(item_uri)

    @staticmethod
    def list_shareable_items(session, share, states, data):
        # All tables from dataset with a column isShared
        # marking the table as part of the shareObject
        tables = (
            session.query(
                DatasetTable.tableUri.label('itemUri'),
                func.coalesce('DatasetTable').label('itemType'),
                DatasetTable.GlueTableName.label('itemName'),
                DatasetTable.description.label('description'),
                ShareObjectItem.shareItemUri.label('shareItemUri'),
                ShareObjectItem.status.label('status'),
                ShareObjectItem.healthStatus.label('healthStatus'),
                ShareObjectItem.healthMessage.label('healthMessage'),
                ShareObjectItem.lastVerificationTime.label('lastVerificationTime'),
                case(
                    [(ShareObjectItem.shareItemUri.isnot(None), True)],
                    else_=False,
                ).label('isShared'),
            )
            .outerjoin(
                ShareObjectItem,
                and_(
                    ShareObjectItem.shareUri == share.shareUri,
                    DatasetTable.tableUri == ShareObjectItem.itemUri,
                ),
            )
            .filter(DatasetTable.datasetUri == share.datasetUri)
        )
        if states:
            tables = tables.filter(ShareObjectItem.status.in_(states))

        # All folders from the dataset with a column isShared
        # marking the folder as part of the shareObject
        locations = (
            session.query(
                DatasetStorageLocation.locationUri.label('itemUri'),
                func.coalesce('DatasetStorageLocation').label('itemType'),
                DatasetStorageLocation.S3Prefix.label('itemName'),
                DatasetStorageLocation.description.label('description'),
                ShareObjectItem.shareItemUri.label('shareItemUri'),
                ShareObjectItem.status.label('status'),
                ShareObjectItem.healthStatus.label('healthStatus'),
                ShareObjectItem.healthMessage.label('healthMessage'),
                ShareObjectItem.lastVerificationTime.label('lastVerificationTime'),
                case(
                    [(ShareObjectItem.shareItemUri.isnot(None), True)],
                    else_=False,
                ).label('isShared'),
            )
            .outerjoin(
                ShareObjectItem,
                and_(
                    ShareObjectItem.shareUri == share.shareUri,
                    DatasetStorageLocation.locationUri == ShareObjectItem.itemUri,
                ),
            )
            .filter(DatasetStorageLocation.datasetUri == share.datasetUri)
        )
        if states:
            locations = locations.filter(ShareObjectItem.status.in_(states))

        s3_buckets = (
            session.query(
                DatasetBucket.bucketUri.label('itemUri'),
                func.coalesce('S3Bucket').label('itemType'),
                DatasetBucket.S3BucketName.label('itemName'),
                DatasetBucket.description.label('description'),
                ShareObjectItem.shareItemUri.label('shareItemUri'),
                ShareObjectItem.status.label('status'),
                ShareObjectItem.healthStatus.label('healthStatus'),
                ShareObjectItem.healthMessage.label('healthMessage'),
                ShareObjectItem.lastVerificationTime.label('lastVerificationTime'),
                case(
                    [(ShareObjectItem.shareItemUri.isnot(None), True)],
                    else_=False,
                ).label('isShared'),
            )
            .outerjoin(
                ShareObjectItem,
                and_(
                    ShareObjectItem.shareUri == share.shareUri,
                    DatasetBucket.bucketUri == ShareObjectItem.itemUri,
                ),
            )
            .filter(DatasetBucket.datasetUri == share.datasetUri)
        )
        if states:
            s3_buckets = s3_buckets.filter(ShareObjectItem.status.in_(states))

        shareable_objects = tables.union(locations, s3_buckets).subquery('shareable_objects')
        query = session.query(shareable_objects)

        if data:
            if data.get('term'):
                term = data.get('term')
                query = query.filter(
                    or_(
                        shareable_objects.c.itemName.ilike(term + '%'),
                        shareable_objects.c.description.ilike(term + '%'),
                    )
                )
            if 'isShared' in data:
                is_shared = data.get('isShared')
                query = query.filter(shareable_objects.c.isShared == is_shared)

            if 'isHealthy' in data:
                # healthy_status = ShareItemHealthStatus.Healthy.value
                query = (
                    query.filter(shareable_objects.c.healthStatus == ShareItemHealthStatus.Healthy.value)
                    if data.get('isHealthy')
                    else query.filter(shareable_objects.c.healthStatus != ShareItemHealthStatus.Healthy.value)
                )

        return paginate(query, data.get('page', 1), data.get('pageSize', 10)).to_dict()


    @staticmethod
    def get_share_data(session, share_uri):
        share: ShareObject = ShareObjectBaseRepository.get_share_by_uri(session, share_uri)

        dataset: S3Dataset = S3DatasetRepository.get_dataset_by_uri(session, share.datasetUri)

        source_environment: Environment = session.query(Environment).get(dataset.environmentUri)
        if not source_environment:
            raise exceptions.ObjectNotFound('SourceEnvironment', dataset.environmentUri)

        target_environment: Environment = session.query(Environment).get(share.environmentUri)
        if not target_environment:
            raise exceptions.ObjectNotFound('TargetEnvironment', share.environmentUri)

        env_group: EnvironmentGroup = (
            session.query(EnvironmentGroup)
            .filter(
                and_(
                    EnvironmentGroup.environmentUri == share.environmentUri,
                    EnvironmentGroup.groupUri == share.groupUri,
                )
            )
            .first()
        )
        if not env_group:
            raise Exception(
                f'Share object Team {share.groupUri} is not a member of the '
                f'environment {target_environment.name}/{target_environment.AwsAccountId}'
            )

        source_env_group: EnvironmentGroup = (
            session.query(EnvironmentGroup)
            .filter(
                and_(
                    EnvironmentGroup.environmentUri == dataset.environmentUri,
                    EnvironmentGroup.groupUri == dataset.SamlAdminGroupName,
                )
            )
            .first()
        )
        if not source_env_group:
            raise Exception(
                f'Share object Team {dataset.SamlAdminGroupName} is not a member of the '
                f'environment {dataset.environmentUri}'
            )

        return (
            source_env_group,
            env_group,
            dataset,
            share,
            source_environment,
            target_environment,
        )

    @staticmethod
    def get_share_data_items(session, share_uri, status=None, healthStatus=None):
        share: ShareObject = ShareObjectBaseRepository.get_share_by_uri(session, share_uri)

        tables = ShareObjectRepository._find_all_share_item(
            session, share, status, healthStatus, DatasetTable, DatasetTable.tableUri
        )

        folders = ShareObjectRepository._find_all_share_item(
            session, share, status, healthStatus, DatasetStorageLocation, DatasetStorageLocation.locationUri
        )

        s3_buckets = ShareObjectRepository._find_all_share_item(
            session, share, status, healthStatus, DatasetBucket, DatasetBucket.bucketUri
        )

        return (
            tables,
            folders,
            s3_buckets,
        )


    @staticmethod
    def other_approved_share_item_table_exists(session, environment_uri, item_uri, share_item_uri):
        share_item_shared_states = ShareItemSM.get_share_item_shared_states()
        return (
            session.query(ShareObject)
            .join(
                ShareObjectItem,
                ShareObject.shareUri == ShareObjectItem.shareUri,
            )
            .filter(
                and_(
                    ShareObject.environmentUri == environment_uri,
                    ShareObjectItem.itemUri == item_uri,
                    ShareObjectItem.shareItemUri != share_item_uri,
                    ShareObjectItem.status.in_(share_item_shared_states),
                )
            )
            .first()
        )

    @staticmethod
    def list_dataset_shares_and_datasets_with_existing_shared_items(
        session, dataset_uri, environment_uri=None, item_type=None
    ) -> [ShareObject]:
        warn(
            'ShareObjectRepository.list_dataset_shares_and_datasets_with_existing_shared_items will be deprecated in v2.6.0',
            DeprecationWarning,
            stacklevel=2,
        )
        # When deprecated, use ist_dataset_shares_with_existing_shared_items instead
        share_item_shared_states = ShareItemSM.get_share_item_shared_states()
        query = (
            session.query(ShareObject)
            .outerjoin(ShareObjectItem, ShareObjectItem.shareUri == ShareObject.shareUri)
            .filter(
                and_(
                    ShareObject.datasetUri == dataset_uri,
                    ShareObject.deleted.is_(None),
                    ShareObjectItem.status.in_(share_item_shared_states),
                )
            )
        )
        if environment_uri:
            query = query.filter(ShareObject.environmentUri == environment_uri)
        if item_type:
            query = query.filter(ShareObjectItem.itemType == item_type)
        shares_datasets = []
        for share in query.all():
            dataset = S3DatasetRepository.get_dataset_by_uri(session, share.datasetUri)
            shares_datasets.append(
                {'shareUri': share.shareUri, 'databaseName': f'{dataset.GlueDatabaseName}_shared_{share.shareUri}'}
            )
        return shares_datasets

    @staticmethod
    def paginate_shared_datasets(session, env_uri, data):
        share_item_shared_states = ShareItemSM.get_share_item_shared_states()
        q = (
            session.query(
                ShareObjectItem.shareUri.label('shareUri'),
                Dataset.datasetUri.label('datasetUri'),
                Dataset.name.label('datasetName'),
                Dataset.description.label('datasetDescription'),
                Environment.environmentUri.label('environmentUri'),
                Environment.name.label('environmentName'),
                ShareObject.created.label('created'),
                ShareObject.principalId.label('principalId'),
                ShareObject.principalType.label('principalType'),
                ShareObjectItem.itemType.label('itemType'),
                ShareObjectItem.GlueDatabaseName.label('GlueDatabaseName'),
                ShareObjectItem.GlueTableName.label('GlueTableName'),
                ShareObjectItem.S3AccessPointName.label('S3AccessPointName'),
                Organization.organizationUri.label('organizationUri'),
                Organization.name.label('organizationName'),
                case(
                    [
                        (
                            ShareObjectItem.itemType == ShareableType.Table.value,
                            func.concat(
                                DatasetTable.GlueDatabaseName,
                                '.',
                                DatasetTable.GlueTableName,
                            ),
                        ),
                        (
                            ShareObjectItem.itemType == ShareableType.StorageLocation.value,
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
                Environment,
                Environment.environmentUri == Dataset.environmentUri,
            )
            .join(
                Organization,
                Organization.organizationUri == Environment.organizationUri,
            )
            .outerjoin(
                DatasetTable,
                ShareObjectItem.itemUri == DatasetTable.tableUri,
            )
            .outerjoin(
                DatasetStorageLocation,
                ShareObjectItem.itemUri == DatasetStorageLocation.locationUri,
            )
            .filter(
                and_(
                    ShareObjectItem.status.in_(share_item_shared_states),
                    ShareObject.environmentUri == env_uri,
                )
            )
        )

        if data.get('datasetUri'):
            dataset_uri = data.get('datasetUri')
            q = q.filter(ShareObject.datasetUri == dataset_uri)

        if data.get('itemTypes', None):
            item_types = data.get('itemTypes')
            q = q.filter(or_(*[ShareObjectItem.itemType == t for t in item_types]))

        if data.get('uniqueShares', False):
            q = q.filter(ShareObject.principalType != PrincipalType.ConsumptionRole.value)
            q = q.distinct(ShareObject.shareUri)

        if data.get('term'):
            term = data.get('term')
            q = q.filter(ShareObjectItem.itemName.ilike('%' + term + '%'))

        return paginate(query=q, page=data.get('page', 1), page_size=data.get('pageSize', 10)).to_dict()

    @staticmethod
    def get_shared_tables(session, dataset) -> List[ShareObjectItem]:
        return (
            session.query(
                DatasetTable.GlueDatabaseName.label('GlueDatabaseName'),
                DatasetTable.GlueTableName.label('GlueTableName'),
                DatasetTable.S3Prefix.label('S3Prefix'),
                DatasetTable.AWSAccountId.label('SourceAwsAccountId'),
                DatasetTable.region.label('SourceRegion'),
                Environment.AwsAccountId.label('TargetAwsAccountId'),
                Environment.region.label('TargetRegion'),
            )
            .join(
                ShareObjectItem,
                and_(ShareObjectItem.itemUri == DatasetTable.tableUri),
            )
            .join(
                ShareObject,
                ShareObject.shareUri == ShareObjectItem.shareUri,
            )
            .join(
                Environment,
                Environment.environmentUri == ShareObject.environmentUri,
            )
            .filter(
                and_(
                    DatasetTable.datasetUri == dataset.datasetUri,
                    DatasetTable.deleted.is_(None),
                    ShareObjectItem.status == ShareObjectStatus.Approved.value,
                )
            )
        ).all()

    @staticmethod
    def get_shared_folders(session, dataset) -> List[DatasetStorageLocation]:
        return (
            session.query(
                DatasetStorageLocation.locationUri.label('locationUri'),
                DatasetStorageLocation.S3BucketName.label('S3BucketName'),
                DatasetStorageLocation.S3Prefix.label('S3Prefix'),
                Environment.AwsAccountId.label('AwsAccountId'),
                Environment.region.label('region'),
            )
            .join(
                ShareObjectItem,
                and_(ShareObjectItem.itemUri == DatasetStorageLocation.locationUri),
            )
            .join(
                ShareObject,
                ShareObject.shareUri == ShareObjectItem.shareUri,
            )
            .join(
                Environment,
                Environment.environmentUri == ShareObject.environmentUri,
            )
            .filter(
                and_(
                    DatasetStorageLocation.datasetUri == dataset.datasetUri,
                    DatasetStorageLocation.deleted.is_(None),
                    ShareObjectItem.status == ShareObjectStatus.Approved.value,
                )
            )
        ).all()


