import logging
from sqlalchemy import and_, or_, func, case
from sqlalchemy.orm import Query
from typing import List

from dataall.base.db import exceptions, paginate
from dataall.core.organizations.db.organization_models import Organization
from dataall.core.environment.db.environment_models import Environment, EnvironmentGroup
from dataall.modules.datasets_base.db.dataset_models import DatasetBase
from dataall.modules.datasets_base.db.dataset_repositories import DatasetBaseRepository
from dataall.modules.shares_base.db.share_object_models import ShareObjectItem, ShareObject
from dataall.modules.shares_base.services.shares_enums import (
    ShareItemHealthStatus,
    PrincipalType,
)

logger = logging.getLogger(__name__)


class ShareObjectRepository:
    @staticmethod
    def save_and_commit(session, share):
        session.add(share)
        session.commit()

    @staticmethod
    def find_share(session, dataset: DatasetBase, env, principal_id, group_uri) -> ShareObject:
        return (
            session.query(ShareObject)
            .filter(
                and_(
                    ShareObject.datasetUri == dataset.datasetUri,
                    ShareObject.principalId == principal_id,
                    ShareObject.environmentUri == env.environmentUri,
                    ShareObject.groupUri == group_uri,
                )
            )
            .first()
        )

    @staticmethod
    def find_sharable_item(session, share_uri, item_uri) -> ShareObjectItem:
        return (
            session.query(ShareObjectItem)
            .filter(
                and_(
                    ShareObjectItem.itemUri == item_uri,
                    ShareObjectItem.shareUri == share_uri,
                )
            )
            .first()
        )

    @staticmethod
    def get_share_by_uri(session, uri):
        share = session.query(ShareObject).get(uri)
        if not share:
            raise exceptions.ObjectNotFound('Share', uri)
        return share

    @staticmethod
    def get_share_item_by_uri(session, uri):
        share_item: ShareObjectItem = session.query(ShareObjectItem).get(uri)
        if not share_item:
            raise exceptions.ObjectNotFound('ShareObjectItem', uri)

        return share_item

    @staticmethod
    def get_share_item_details(session, share_type_model, item_uri):  # TODO CHECK THAT IT WORKS
        return session.query(share_type_model).get(item_uri)

    @staticmethod
    def remove_share_object_item(session, share_item):
        session.delete(share_item)
        return True

    @staticmethod
    def get_share_data(session, share_uri):
        share: ShareObject = ShareObjectRepository.get_share_by_uri(session, share_uri)
        dataset: DatasetBase = DatasetBaseRepository.get_dataset_by_uri(session, share.datasetUri)

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
            share,
            dataset,
            source_environment,
            target_environment,
            source_env_group,
            env_group,
        )

    @staticmethod
    def get_share_data_items_by_type(session, share, share_type_model, share_type_uri, status=None, healthStatus=None):
        logger.info(f'Getting share items {status=}, {healthStatus=} for {share_type_model=} with {share_type_uri=}')
        query = (
            session.query(share_type_model)
            .join(
                ShareObjectItem,
                ShareObjectItem.itemUri == share_type_uri,
            )
            .join(
                ShareObject,
                ShareObject.shareUri == ShareObjectItem.shareUri,
            )
            .filter(
                and_(
                    ShareObject.datasetUri == share.datasetUri,
                    ShareObject.environmentUri == share.environmentUri,
                    ShareObject.shareUri == share.shareUri,
                )
            )
        )
        if status:
            query = query.filter(ShareObjectItem.status == status)
        if healthStatus:
            query = query.filter(ShareObjectItem.healthStatus == healthStatus)
        return query.all()

    @staticmethod
    def get_all_share_items_in_share(session, share_uri, status=None, healthStatus=None):
        query = (
            session.query(ShareObjectItem)
            .join(
                ShareObject,
                ShareObject.shareUri == ShareObjectItem.shareUri,
            )
            .filter(
                and_(
                    ShareObject.shareUri == share_uri,
                )
            )
        )
        if status:
            query = query.filter(ShareObjectItem.status.in_(status))
        if healthStatus:
            query = query.filter(ShareObjectItem.healthStatus.in_(healthStatus))
        return query.all()

    @staticmethod
    def list_all_active_share_objects(session) -> [ShareObject]:
        return session.query(ShareObject).filter(ShareObject.deleted.is_(None)).all()

    @staticmethod
    def list_user_received_share_requests(session, username, groups, data=None):
        query = (
            session.query(ShareObject)
            .join(
                DatasetBase,
                DatasetBase.datasetUri == ShareObject.datasetUri,
            )
            .filter(
                or_(
                    DatasetBase.businessOwnerEmail == username,
                    DatasetBase.businessOwnerDelegationEmails.contains(f'{{{username}}}'),
                    DatasetBase.stewards.in_(groups),
                    DatasetBase.SamlAdminGroupName.in_(groups),
                )
            )
        )

        if data and data.get('status'):
            if len(data.get('status')) > 0:
                query = query.filter(ShareObject.status.in_(data.get('status')))
        if data and data.get('dataset_owners'):
            if len(data.get('dataset_owners')) > 0:
                query = query.filter(DatasetBase.SamlAdminGroupName.in_(data.get('dataset_owners')))
        if data and data.get('datasets_uris'):
            if len(data.get('datasets_uris')) > 0:
                query = query.filter(ShareObject.datasetUri.in_(data.get('datasets_uris')))
        if data and data.get('share_requesters'):
            if len(data.get('share_requesters')) > 0:
                query = query.filter(ShareObject.groupUri.in_(data.get('share_requesters')))
        if data and data.get('share_iam_roles'):
            if len(data.get('share_iam_roles')) > 0:
                query = query.filter(ShareObject.principalIAMRoleName.in_(data.get('share_iam_roles')))
        return paginate(query.order_by(ShareObject.shareUri), data.get('page', 1), data.get('pageSize', 10)).to_dict()

    @staticmethod
    def list_user_sent_share_requests(session, username, groups, data=None):
        query = (
            session.query(ShareObject)
            .join(
                Environment,
                Environment.environmentUri == ShareObject.environmentUri,
            )
            .join(
                DatasetBase,
                DatasetBase.datasetUri == ShareObject.datasetUri,
            )
            .filter(
                or_(
                    ShareObject.owner == username,
                    and_(
                        ShareObject.groupUri.in_(groups),
                        ShareObject.principalType.in_([PrincipalType.Group.value, PrincipalType.ConsumptionRole.value]),
                    ),
                )
            )
        )
        if data and data.get('status'):
            if len(data.get('status')) > 0:
                query = query.filter(ShareObject.status.in_(data.get('status')))
        if data and data.get('dataset_owners'):
            if len(data.get('dataset_owners')) > 0:
                query = query.filter(DatasetBase.SamlAdminGroupName.in_(data.get('dataset_owners')))
        if data and data.get('datasets_uris'):
            if len(data.get('datasets_uris')) > 0:
                query = query.filter(ShareObject.datasetUri.in_(data.get('datasets_uris')))
        if data and data.get('share_requesters'):
            if len(data.get('share_requesters')) > 0:
                query = query.filter(ShareObject.groupUri.in_(data.get('share_requesters')))
        if data and data.get('share_iam_roles'):
            if len(data.get('share_iam_roles')) > 0:
                query = query.filter(ShareObject.principalIAMRoleName.in_(data.get('share_iam_roles')))
        return paginate(query.order_by(ShareObject.shareUri), data.get('page', 1), data.get('pageSize', 10)).to_dict()

    @staticmethod
    def paginate_shared_datasets(session, env_uri, data, share_item_shared_states):
        q = (
            session.query(
                ShareObjectItem.shareUri.label('shareUri'),
                DatasetBase.datasetUri.label('datasetUri'),
                DatasetBase.name.label('datasetName'),
                DatasetBase.description.label('datasetDescription'),
                Environment.environmentUri.label('environmentUri'),
                Environment.name.label('environmentName'),
                ShareObject.created.label('created'),
                ShareObject.principalId.label('principalId'),
                ShareObject.principalType.label('principalType'),
                ShareObject.environmentUri.label('targetEnvironmentUri'),
                ShareObjectItem.itemType.label('itemType'),
                ShareObjectItem.itemName.label('itemName'),
                Organization.organizationUri.label('organizationUri'),
                Organization.name.label('organizationName'),
            )
            .join(
                ShareObject,
                ShareObject.shareUri == ShareObjectItem.shareUri,
            )
            .join(
                DatasetBase,
                ShareObject.datasetUri == DatasetBase.datasetUri,
            )
            .join(
                Environment,
                Environment.environmentUri == DatasetBase.environmentUri,
            )
            .join(
                Organization,
                Organization.organizationUri == Environment.organizationUri,
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
            q = q.order_by(ShareObject.shareUri).distinct(ShareObject.shareUri)
        else:
            q = q.order_by(ShareObjectItem.itemName).distinct()

        if data.get('term'):
            term = data.get('term')
            q = q.filter(ShareObjectItem.itemName.ilike('%' + term + '%'))

        return paginate(query=q, page=data.get('page', 1), page_size=data.get('pageSize', 10)).to_dict()

    ######### TODO: TEST
    @staticmethod
    def list_shareable_items_of_type(session, share, share_type_model, share_type_uri, status=None):  # TODO
        logger.info(f'Getting all shareable items {status=}, for {share_type_model=}')
        query = (
            session.query(
                share_type_model,
                share_type_uri.label('itemUri'),
                func.coalesce(str(share_type_uri).split('.')[-1]).label('itemType'),
                share_type_model.description.label('description'),
                share_type_model.name.label(
                    'itemName'
                ),  # TODO: THE ONLY ITEM MISSING IS THE ITEMNAME - in reality it is the gluetablename, the s3prefix and the s3 bucket
            )
            .outerjoin(
                ShareObjectItem,
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
            .join(
                ShareObject,
                ShareObject.shareUri == ShareObjectItem.shareUri,
            )
            .filter(
                and_(
                    ShareObject.datasetUri == share.datasetUri,
                    ShareObject.environmentUri == share.environmentUri,
                    ShareObject.shareUri == share.shareUri,
                )
            )
        )
        if status:
            query = query.filter(ShareObjectItem.status.in_(status))
        return query

    @staticmethod
    def paginated_list_shareable_items(session, subqueries: List[Query], data: dict = None):
        if len(subqueries) == 1:
            shareable_objects = subqueries[0].subquery('shareable_objects')
        else:
            shareable_objects = subqueries[0].union(*subqueries[1:]).subquery('shareable_objects')
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
                query = (
                    query.filter(shareable_objects.c.healthStatus == ShareItemHealthStatus.Healthy.value)
                    if data.get('isHealthy')
                    else query.filter(shareable_objects.c.healthStatus != ShareItemHealthStatus.Healthy.value)
                )

        return paginate(
            query.order_by(shareable_objects.c.itemName).distinct(), data.get('page', 1), data.get('pageSize', 10)
        ).to_dict()

    # @staticmethod
    # def list_shareable_items(session, share, states, data): #TODO
    #     # All tables from dataset with a column isShared
    #     # marking the table as part of the shareObject
    #     tables = (
    #         session.query(
    #             DatasetTable.tableUri.label('itemUri'),
    #             func.coalesce('DatasetTable').label('itemType'),
    #             DatasetTable.GlueTableName.label('itemName'),
    #             DatasetTable.description.label('description'),
    #             ShareObjectItem.shareItemUri.label('shareItemUri'),
    #             ShareObjectItem.status.label('status'),
    #             ShareObjectItem.healthStatus.label('healthStatus'),
    #             ShareObjectItem.healthMessage.label('healthMessage'),
    #             ShareObjectItem.lastVerificationTime.label('lastVerificationTime'),
    #             case(
    #                 [(ShareObjectItem.shareItemUri.isnot(None), True)],
    #                 else_=False,
    #             ).label('isShared'),
    #         )
    #         .outerjoin(
    #             ShareObjectItem,
    #             and_(
    #                 ShareObjectItem.shareUri == share.shareUri,
    #                 DatasetTable.tableUri == ShareObjectItem.itemUri,
    #             ),
    #         )
    #         .filter(DatasetTable.datasetUri == share.datasetUri)
    #     )
    #     if states:
    #         tables = tables.filter(ShareObjectItem.status.in_(states))
    #
    #     # All folders from the dataset with a column isShared
    #     # marking the folder as part of the shareObject
    #     locations = (
    #         session.query(
    #             DatasetStorageLocation.locationUri.label('itemUri'),
    #             func.coalesce('DatasetStorageLocation').label('itemType'),
    #             DatasetStorageLocation.S3Prefix.label('itemName'),
    #             DatasetStorageLocation.description.label('description'),
    #             ShareObjectItem.shareItemUri.label('shareItemUri'),
    #             ShareObjectItem.status.label('status'),
    #             ShareObjectItem.healthStatus.label('healthStatus'),
    #             ShareObjectItem.healthMessage.label('healthMessage'),
    #             ShareObjectItem.lastVerificationTime.label('lastVerificationTime'),
    #             case(
    #                 [(ShareObjectItem.shareItemUri.isnot(None), True)],
    #                 else_=False,
    #             ).label('isShared'),
    #         )
    #         .outerjoin(
    #             ShareObjectItem,
    #             and_(
    #                 ShareObjectItem.shareUri == share.shareUri,
    #                 DatasetStorageLocation.locationUri == ShareObjectItem.itemUri,
    #             ),
    #         )
    #         .filter(DatasetStorageLocation.datasetUri == share.datasetUri)
    #     )
    #     if states:
    #         locations = locations.filter(ShareObjectItem.status.in_(states))
    #
    #     s3_buckets = (
    #         session.query(
    #             DatasetBucket.bucketUri.label('itemUri'),
    #             func.coalesce('S3Bucket').label('itemType'),
    #             DatasetBucket.S3BucketName.label('itemName'),
    #             DatasetBucket.description.label('description'),
    #             ShareObjectItem.shareItemUri.label('shareItemUri'),
    #             ShareObjectItem.status.label('status'),
    #             ShareObjectItem.healthStatus.label('healthStatus'),
    #             ShareObjectItem.healthMessage.label('healthMessage'),
    #             ShareObjectItem.lastVerificationTime.label('lastVerificationTime'),
    #             case(
    #                 [(ShareObjectItem.shareItemUri.isnot(None), True)],
    #                 else_=False,
    #             ).label('isShared'),
    #         )
    #         .outerjoin(
    #             ShareObjectItem,
    #             and_(
    #                 ShareObjectItem.shareUri == share.shareUri,
    #                 DatasetBucket.bucketUri == ShareObjectItem.itemUri,
    #             ),
    #         )
    #         .filter(DatasetBucket.datasetUri == share.datasetUri)
    #     )
    #     if states:
    #         s3_buckets = s3_buckets.filter(ShareObjectItem.status.in_(states))
    #
    #     shareable_objects = tables.union(locations, s3_buckets).subquery('shareable_objects')
    #     query = session.query(shareable_objects)
    #
    #     if data:
    #         if data.get('term'):
    #             term = data.get('term')
    #             query = query.filter(
    #                 or_(
    #                     shareable_objects.c.itemName.ilike(term + '%'),
    #                     shareable_objects.c.description.ilike(term + '%'),
    #                 )
    #             )
    #         if 'isShared' in data:
    #             is_shared = data.get('isShared')
    #             query = query.filter(shareable_objects.c.isShared == is_shared)
    #
    #         if 'isHealthy' in data:
    #             # healthy_status = ShareItemHealthStatus.Healthy.value
    #             query = (
    #                 query.filter(shareable_objects.c.healthStatus == ShareItemHealthStatus.Healthy.value)
    #                 if data.get('isHealthy')
    #                 else query.filter(shareable_objects.c.healthStatus != ShareItemHealthStatus.Healthy.value)
    #             )
    #
    #     return paginate(
    #         query.order_by(shareable_objects.c.itemName).distinct(), data.get('page', 1), data.get('pageSize', 10)
    #     ).to_dict()
    #
