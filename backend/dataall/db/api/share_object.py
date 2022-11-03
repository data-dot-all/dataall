import logging

from sqlalchemy import and_, or_, func, case

from . import (
    has_resource_perm,
    ResourcePolicy,
    Environment,
)
from .. import api
from .. import models, exceptions, permissions, paginate
from ..models.Enums import ShareObjectStatus, ShareableType, PrincipalType

logger = logging.getLogger(__name__)


class ShareObject:
    @staticmethod
    @has_resource_perm(permissions.CREATE_SHARE_OBJECT)
    def create_share_object(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ) -> models.ShareObject:
        if not data:
            raise exceptions.RequiredParameter(data)
        if not data.get('principalId'):
            raise exceptions.RequiredParameter('principalId')
        if not data.get('datasetUri'):
            raise exceptions.RequiredParameter('datasetUri')

        principalId = data['principalId']
        principalType = data['principalType']
        datasetUri = data['datasetUri']
        environmentUri = uri
        itemUri = data.get('itemUri')
        itemType = data.get('itemType')

        dataset: models.Dataset = data.get(
            'dataset', api.Dataset.get_dataset_by_uri(session, datasetUri)
        )
        environment: models.Environment = data.get(
            'environment',
            api.Environment.get_environment_by_uri(session, environmentUri),
        )

        if (
            dataset.stewards == principalId or dataset.SamlAdminGroupName == principalId
        ) and environment.environmentUri == dataset.environmentUri:
            raise exceptions.UnauthorizedOperation(
                action=permissions.CREATE_SHARE_OBJECT,
                message=f'Team: {principalId} is managing the dataset {dataset.name}',
            )

        ShareObject.validate_group_membership(
            session=session,
            username=username,
            groups=groups,
            share_object_group=principalId,
            environment_uri=uri,
        )

        share: models.ShareObject = (
            session.query(models.ShareObject)
            .filter(
                and_(
                    models.ShareObject.datasetUri == datasetUri,
                    models.ShareObject.principalId == principalId,
                    models.ShareObject.environmentUri == environmentUri,
                )
            )
            .first()
        )
        if not share:
            share = models.ShareObject(
                datasetUri=dataset.datasetUri,
                environmentUri=environment.environmentUri,
                owner=username,
                principalId=principalId,
                principalType=principalType,
                status=ShareObjectStatus.Draft.value,
            )
            session.add(share)
            session.commit()

        if itemUri:
            item = None
            if itemType:
                if itemType == ShareableType.StorageLocation.value:
                    item = session.query(models.DatasetStorageLocation).get(itemUri)
                if itemType == ShareableType.Table.value:
                    item = session.query(models.DatasetTable).get(itemUri)

            share_item = (
                session.query(models.ShareObjectItem)
                .filter(
                    and_(
                        models.ShareObjectItem.shareUri == share.shareUri,
                        models.ShareObjectItem.itemUri == itemUri,
                    )
                )
                .first()
            )
            if not share_item and item:
                new_share_item: models.ShareObjectItem = models.ShareObjectItem(
                    shareUri=share.shareUri,
                    itemUri=itemUri,
                    itemType=itemType,
                    itemName=item.name,
                    status=ShareObjectStatus.Draft.value,
                    owner=username,
                    GlueDatabaseName=dataset.GlueDatabaseName
                    if itemType == ShareableType.Table.value
                    else '',
                    GlueTableName=item.GlueTableName
                    if itemType == ShareableType.Table.value
                    else '',
                    S3AccessPointName=f'{share.datasetUri}-{share.principalId}'.lower()
                    if itemType == ShareableType.StorageLocation.value
                    else '',
                )
                session.add(new_share_item)

        activity = models.Activity(
            action='SHARE_OBJECT:CREATE',
            label='SHARE_OBJECT:CREATE',
            owner=username,
            summary=f'{username} created a share object for the {dataset.name} in {environment.name} for the group {principalId}',
            targetUri=dataset.datasetUri,
            targetType='dataset',
        )
        session.add(activity)

        ResourcePolicy.attach_resource_policy(
            session=session,
            group=principalId,
            permissions=permissions.SHARE_OBJECT_REQUESTER,
            resource_uri=share.shareUri,
            resource_type=models.ShareObject.__name__,
        )
        ResourcePolicy.attach_resource_policy(
            session=session,
            group=dataset.SamlAdminGroupName,
            permissions=permissions.SHARE_OBJECT_REQUESTER,
            resource_uri=share.shareUri,
            resource_type=models.ShareObject.__name__,
        )
        ResourcePolicy.attach_resource_policy(
            session=session,
            group=dataset.stewards,
            permissions=permissions.SHARE_OBJECT_APPROVER,
            resource_uri=share.shareUri,
            resource_type=models.ShareObject.__name__,
        )
        if dataset.SamlAdminGroupName != environment.SamlGroupName:
            ResourcePolicy.attach_resource_policy(
                session=session,
                group=environment.SamlGroupName,
                permissions=permissions.SHARE_OBJECT_REQUESTER,
                resource_uri=share.shareUri,
                resource_type=models.ShareObject.__name__,
            )
        return share

    @staticmethod
    def validate_group_membership(
        session, environment_uri, share_object_group, username, groups
    ):
        if share_object_group and share_object_group not in groups:
            raise exceptions.UnauthorizedOperation(
                action=permissions.CREATE_SHARE_OBJECT,
                message=f'User: {username} is not a member of the team {share_object_group}',
            )
        if share_object_group not in Environment.list_environment_groups(
            session=session,
            username=username,
            groups=groups,
            uri=environment_uri,
            data=None,
            check_perm=True,
        ):
            raise exceptions.UnauthorizedOperation(
                action=permissions.CREATE_SHARE_OBJECT,
                message=f'Team: {share_object_group} is not a member of the environment {environment_uri}',
            )

    @staticmethod
    @has_resource_perm(permissions.SUBMIT_SHARE_OBJECT)
    def submit_share_object(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ) -> models.ShareObject:
        share = ShareObject.get_share_by_uri(session, uri)
        dataset = api.Dataset.get_dataset_by_uri(session, share.datasetUri)
        if share.status == ShareObjectStatus.PendingApproval.value:
            raise exceptions.UnauthorizedOperation(
                action=permissions.SUBMIT_SHARE_OBJECT,
                message='ShareObject is in PendingApproval state',
            )
        (
            session.query(models.ShareObjectItem)
            .filter(
                and_(
                    models.ShareObjectItem.shareUri == uri,
                    models.ShareObjectItem.status != ShareObjectStatus.Approved.value,
                )
            )
            .update(
                {models.ShareObjectItem.status: ShareObjectStatus.PendingApproval.value}
            )
        )
        share.status = ShareObjectStatus.PendingApproval.value
        api.Notification.notify_share_object_submission(
            session, username, dataset, share
        )
        return share

    @staticmethod
    @has_resource_perm(permissions.APPROVE_SHARE_OBJECT)
    def approve_share_object(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ) -> models.ShareObject:
        share = ShareObject.get_share_by_uri(session, uri)

        dataset = api.Dataset.get_dataset_by_uri(session, share.datasetUri)

        if share.status != ShareObjectStatus.PendingApproval.value:
            raise exceptions.UnauthorizedOperation(
                action=permissions.APPROVE_SHARE_OBJECT,
                message='ShareObject is not in PendingApproval state',
            )

        (
            session.query(models.ShareObjectItem)
            .filter(
                and_(
                    models.ShareObjectItem.shareUri == uri,
                )
            )
            .update(
                {
                    models.ShareObjectItem.status: ShareObjectStatus.Approved.value,
                }
            )
        )

        share.status = ShareObjectStatus.Approved.value

        ResourcePolicy.attach_resource_policy(
            session=session,
            group=share.principalId,
            permissions=permissions.DATASET_READ,
            resource_uri=dataset.datasetUri,
            resource_type=models.Dataset.__name__,
        )

        api.Notification.notify_share_object_approval(session, username, dataset, share)
        return share

    @staticmethod
    @has_resource_perm(permissions.REJECT_SHARE_OBJECT)
    def reject_share_object(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ) -> models.ShareObject:

        share = ShareObject.get_share_by_uri(session, uri)

        dataset = api.Dataset.get_dataset_by_uri(session, share.datasetUri)

        if share.status == ShareObjectStatus.Rejected.value:
            raise exceptions.UnauthorizedOperation(
                action=permissions.REJECT_SHARE_OBJECT,
                message='ShareObject is not in Rejected state',
            )
        (
            session.query(models.ShareObjectItem)
            .filter(
                and_(
                    models.ShareObjectItem.shareUri == uri,
                )
            )
            .update(
                {
                    models.ShareObjectItem.status: ShareObjectStatus.Rejected.value,
                }
            )
        )
        share.status = ShareObjectStatus.Rejected.value
        ResourcePolicy.delete_resource_policy(
            session=session,
            group=share.principalId,
            resource_uri=dataset.datasetUri,
        )
        api.Notification.notify_share_object_approval(session, username, dataset, share)
        return share

    @staticmethod
    @has_resource_perm(permissions.GET_SHARE_OBJECT)
    def get_share_object(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ):
        share = session.query(models.ShareObject).get(uri)
        if not share:
            raise exceptions.ObjectNotFound('Share', uri)

        return share

    @staticmethod
    @has_resource_perm(permissions.GET_SHARE_OBJECT)
    def get_share_item(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ):
        share_item: models.ShareObjectItem = data.get(
            'share_item',
            ShareObject.get_share_item_by_uri(session, data['shareItemUri']),
        )
        if share_item.itemType == ShareableType.Table.value:
            return session.query(models.DatasetTable).get(share_item.itemUri)
        if share_item.itemType == ShareableType.StorageLocation:
            return session.Query(models.DatasetStorageLocation).get(share_item.itemUri)

    @staticmethod
    def get_share_by_uri(session, uri):
        share = session.query(models.ShareObject).get(uri)
        if not share:
            raise exceptions.ObjectNotFound('Share', uri)
        return share

    @staticmethod
    def get_share_by_dataset_attributes(session, dataset_uri, dataset_owner):
        share: models.ShareObject = (
            session.query(models.ShareObject)
            .filter(models.ShareObject.datasetUri == dataset_uri)
            .filter(models.ShareObject.owner == dataset_owner)
            .first()
        )
        return share

    @staticmethod
    @has_resource_perm(permissions.ADD_ITEM)
    def add_share_object_item(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ) -> models.ShareObjectItem:
        itemType = data.get('itemType')
        itemUri = data.get('itemUri')
        item = None
        share: models.ShareObject = session.query(models.ShareObject).get(uri)
        dataset: models.Dataset = session.query(models.Dataset).get(share.datasetUri)
        target_environment: models.Environment = session.query(models.Environment).get(
            share.environmentUri
        )

        if itemType == ShareableType.Table.value:
            item: models.DatasetTable = session.query(models.DatasetTable).get(itemUri)
            if item and item.region != target_environment.region:
                raise exceptions.UnauthorizedOperation(
                    action=permissions.ADD_ITEM,
                    message=f'Lake Formation cross region sharing is not supported. '
                    f'Table {item.GlueTableName} is in {item.region} and target environment '
                    f'{target_environment.name} is in {target_environment.region} ',
                )

        elif itemType == ShareableType.StorageLocation.value:
            item = session.query(models.DatasetStorageLocation).get(itemUri)

        if not item:
            raise exceptions.ObjectNotFound('ShareObjectItem', itemUri)

        shareItem: models.ShareObjectItem = (
            session.query(models.ShareObjectItem)
            .filter(
                and_(
                    models.ShareObjectItem.shareUri == uri,
                    models.ShareObjectItem.itemUri == itemUri,
                )
            )
            .first()
        )

        if not shareItem:
            shareItem = models.ShareObjectItem(
                shareUri=uri,
                itemUri=itemUri,
                itemType=itemType,
                itemName=item.name,
                status=ShareObjectStatus.Draft.value,
                owner=username,
                GlueDatabaseName=dataset.GlueDatabaseName
                if itemType == ShareableType.Table.value
                else '',
                GlueTableName=item.GlueTableName
                if itemType == ShareableType.Table.value
                else '',
                S3AccessPointName=f'{share.datasetUri}-{share.principalId}'.lower()
                if itemType == ShareableType.StorageLocation.value
                else '',
            )
            session.add(shareItem)
            share.status = ShareObjectStatus.Draft.value

        return shareItem

    @staticmethod
    @has_resource_perm(permissions.REMOVE_ITEM)
    def remove_share_object_item(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ) -> bool:
        share_item: models.ShareObjectItem = data.get(
            'share_item',
            ShareObject.get_share_item_by_uri(session, data['shareItemUri']),
        )
        share: models.ShareObject = data.get(
            'share',
            ShareObject.get_share_by_uri(session, uri),
        )
        session.delete(share_item)
        share.status = ShareObjectStatus.Draft.value
        return True

    @staticmethod
    @has_resource_perm(permissions.DELETE_SHARE_OBJECT)
    def delete_share_object(session, username, groups, uri, data=None, check_perm=None):
        share: models.ShareObject = ShareObject.get_share_by_uri(session, uri)
        shared_items = session.query(models.ShareObjectItem).filter(
            models.ShareObjectItem.shareUri == share.shareUri
        ).all()
        if shared_items:
            raise exceptions.ShareItemsFound(
                action='Delete share object',
                message='Delete all shared items before proceeding',
            )
        session.delete(share)
        return True

    @staticmethod
    def get_share_item_by_uri(session, uri):
        share_item: models.ShareObjectItem = session.query(models.ShareObjectItem).get(
            uri
        )
        if not share_item:
            raise exceptions.ObjectNotFound('ShareObjectItem', uri)

    @staticmethod
    @has_resource_perm(permissions.LIST_SHARED_ITEMS)
    def list_shared_items(session, username, groups, uri, data=None, check_perm=None):
        share: models.ShareObject = ShareObject.get_share_by_uri(session, uri)
        query = session.query(models.ShareObjectItem).filter(
            models.ShareObjectItem.shareUri == share.shareUri,
        )
        return paginate(
            query, page=data.get('page', 1), page_size=data.get('pageSize', 5)
        ).to_dict()

    @staticmethod
    def list_shareable_items(
        session, username, groups, uri, data=None, check_perm=None
    ):

        share: models.ShareObject = data.get(
            'share', ShareObject.get_share_by_uri(session, uri)
        )
        datasetUri = share.datasetUri

        # All tables from dataset with a column isShared
        # marking the table as part of the shareObject
        tables = (
            session.query(
                models.DatasetTable.tableUri.label('itemUri'),
                func.coalesce('DatasetTable').label('itemType'),
                models.DatasetTable.GlueTableName.label('itemName'),
                models.DatasetTable.description.label('description'),
                models.ShareObjectItem.shareItemUri.label('shareItemUri'),
                models.ShareObjectItem.status.label('status'),
                case(
                    [(models.ShareObjectItem.shareItemUri.isnot(None), True)],
                    else_=False,
                ).label('isShared'),
            )
            .outerjoin(
                models.ShareObjectItem,
                and_(
                    models.ShareObjectItem.shareUri == share.shareUri,
                    models.DatasetTable.tableUri == models.ShareObjectItem.itemUri,
                ),
            )
            .filter(models.DatasetTable.datasetUri == datasetUri)
        )

        # All folders from the dataset with a column isShared
        # marking the folder as part of the shareObject
        locations = (
            session.query(
                models.DatasetStorageLocation.locationUri.label('itemUri'),
                func.coalesce('DatasetStorageLocation').label('itemType'),
                models.DatasetStorageLocation.S3Prefix.label('itemName'),
                models.DatasetStorageLocation.description.label('description'),
                models.ShareObjectItem.shareItemUri.label('shareItemUri'),
                models.ShareObjectItem.status.label('status'),
                case(
                    [(models.ShareObjectItem.shareItemUri.isnot(None), True)],
                    else_=False,
                ).label('isShared'),
            )
            .outerjoin(
                models.ShareObjectItem,
                and_(
                    models.ShareObjectItem.shareUri == share.shareUri,
                    models.DatasetStorageLocation.locationUri
                    == models.ShareObjectItem.itemUri,
                ),
            )
            .filter(models.DatasetStorageLocation.datasetUri == datasetUri)
        )

        shareable_objects = tables.union(locations).subquery('shareable_objects')
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
            if 'isShared' in data.keys():
                isShared = data.get('isShared')
                query = query.filter(shareable_objects.c.isShared == isShared)

        return paginate(query, data.get('page', 1), data.get('pageSize', 10)).to_dict()

    @staticmethod
    def list_user_received_share_requests(
        session, username, groups, uri, data=None, check_perm=None
    ):
        query = (
            session.query(models.ShareObject)
            .join(
                models.Dataset,
                models.Dataset.datasetUri == models.ShareObject.datasetUri,
            )
            .filter(
                or_(
                    models.Dataset.businessOwnerEmail == username,
                    models.Dataset.businessOwnerDelegationEmails.contains(
                        f'{{{username}}}'
                    ),
                    models.Dataset.stewards.in_(groups),
                )
            )
        )
        return paginate(query, data.get('page', 1), data.get('pageSize', 10)).to_dict()

    @staticmethod
    def list_user_sent_share_requests(
        session, username, groups, uri, data=None, check_perm=None
    ):
        query = (
            session.query(models.ShareObject)
            .join(
                models.Environment,
                models.Environment.environmentUri == models.ShareObject.environmentUri,
            )
            .filter(
                or_(
                    models.ShareObject.owner == username,
                    and_(
                        models.Environment.SamlGroupName.in_(groups),
                        models.ShareObject.principalType == PrincipalType.Group.value,
                    ),
                )
            )
        )
        return paginate(query, data.get('page', 1), data.get('pageSize', 10)).to_dict()

    @staticmethod
    def get_share_by_dataset_and_environment(session, dataset_uri, environment_uri):
        environment_groups = session.query(models.EnvironmentGroup).filter(
            models.EnvironmentGroup.environmentUri == environment_uri
        )
        groups = [g.groupUri for g in environment_groups]
        share = session.query(models.ShareObject).filter(
            and_(
                models.ShareObject.datasetUri == dataset_uri,
                models.ShareObject.environmentUri == environment_uri,
                models.ShareObject.principalId.in_(groups),
            )
        )
        if not share:
            raise exceptions.ObjectNotFound('Share', f'{dataset_uri}/{environment_uri}')
        return share

    @staticmethod
    def update_share_item_status(
        session,
        share_item: models.ShareObjectItem,
        status: str,
    ) -> models.ShareObjectItem:

        logger.info(f'Updating share item status to {status}')
        share_item.status = status
        session.commit()
        return share_item

    @staticmethod
    def find_share_item_by_table(
        session,
        share: models.ShareObject,
        table: models.DatasetTable,
    ) -> models.ShareObjectItem:
        share_item: models.ShareObjectItem = (
            session.query(models.ShareObjectItem)
            .filter(
                and_(
                    models.ShareObjectItem.itemUri == table.tableUri,
                    models.ShareObjectItem.shareUri == share.shareUri,
                )
            )
            .first()
        )
        return share_item

    @staticmethod
    def find_share_item_by_folder(
        session,
        share: models.ShareObject,
        folder: models.DatasetStorageLocation,
    ) -> models.ShareObjectItem:
        share_item: models.ShareObjectItem = (
            session.query(models.ShareObjectItem)
            .filter(
                and_(
                    models.ShareObjectItem.itemUri == folder.locationUri,
                    models.ShareObjectItem.shareUri == share.shareUri,
                )
            )
            .first()
        )
        return share_item

    @staticmethod
    def get_share_data(session, share_uri, status):
        share: models.ShareObject = session.query(models.ShareObject).get(share_uri)
        if not share:
            raise exceptions.ObjectNotFound('Share', share_uri)

        dataset: models.Dataset = session.query(models.Dataset).get(share.datasetUri)
        if not dataset:
            raise exceptions.ObjectNotFound('Dataset', share.datasetUri)

        source_environment: models.Environment = session.query(models.Environment).get(
            dataset.environmentUri
        )
        if not source_environment:
            raise exceptions.ObjectNotFound('SourceEnvironment', dataset.environmentUri)

        target_environment: models.Environment = session.query(models.Environment).get(
            share.environmentUri
        )
        if not target_environment:
            raise exceptions.ObjectNotFound('TargetEnvironment', share.environmentUri)

        shared_tables = (
            session.query(models.DatasetTable)
            .join(
                models.ShareObjectItem,
                models.ShareObjectItem.itemUri == models.DatasetTable.tableUri,
            )
            .join(
                models.ShareObject,
                models.ShareObject.shareUri == models.ShareObjectItem.shareUri,
            )
            .filter(
                and_(
                    models.ShareObject.datasetUri == dataset.datasetUri,
                    models.ShareObject.environmentUri
                    == target_environment.environmentUri,
                    models.ShareObject.status.in_(status),
                    models.ShareObject.shareUri == share_uri,
                )
            )
            .all()
        )

        shared_folders = (
            session.query(models.DatasetStorageLocation)
            .join(
                models.ShareObjectItem,
                models.ShareObjectItem.itemUri == models.DatasetStorageLocation.locationUri,
            )
            .join(
                models.ShareObject,
                models.ShareObject.shareUri == models.ShareObjectItem.shareUri,
            )
            .filter(
                and_(
                    models.ShareObject.datasetUri == dataset.datasetUri,
                    models.ShareObject.environmentUri
                    == target_environment.environmentUri,
                    models.ShareObject.status.in_(status),
                    models.ShareObject.shareUri == share_uri,
                )
            )
            .all()
        )

        env_group: models.EnvironmentGroup = (
            session.query(models.EnvironmentGroup)
            .filter(
                and_(
                    models.EnvironmentGroup.environmentUri == share.environmentUri,
                    models.EnvironmentGroup.groupUri == share.principalId,
                )
            )
            .first()
        )
        if not env_group:
            raise Exception(
                f'Share object Team {share.principalId} is not a member of the '
                f'environment {target_environment.name}/{target_environment.AwsAccountId}'
            )

        source_env_group: models.EnvironmentGroup = (
            session.query(models.EnvironmentGroup)
            .filter(
                and_(
                    models.EnvironmentGroup.environmentUri == dataset.environmentUri,
                    models.EnvironmentGroup.groupUri == dataset.SamlAdminGroupName,
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
            shared_tables,
            shared_folders,
            source_environment,
            target_environment,
        )

    @staticmethod
    def other_approved_share_object_exists(session, environment_uri, dataset_uri):
        return (
            session.query(models.ShareObject)
            .filter(
                and_(
                    models.Environment.environmentUri == environment_uri,
                    models.ShareObject.status
                    == models.Enums.ShareObjectStatus.Approved.value,
                    models.ShareObject.datasetUri == dataset_uri,
                )
            )
            .all()
        )

    @staticmethod
    def is_shared_table(session, environment_uri, dataset_uri, table_name):
        return (
            session.query(models.ShareObjectItem)
            .join(
                models.ShareObject,
                models.ShareObjectItem.shareUri == models.ShareObject.shareUri,
            )
            .filter(
                and_(
                    models.ShareObjectItem.GlueTableName == table_name,
                    models.ShareObject.datasetUri == dataset_uri,
                    models.ShareObject.status == models.Enums.ShareObjectStatus.Approved.value,
                    models.ShareObject.environmentUri == environment_uri,
                )
            )
            .first()
        )
