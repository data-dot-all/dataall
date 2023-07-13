from dataall.aws.handlers.service_handlers import Worker
from dataall.base.context import get_context
from dataall.core.activity.db.activity_models import Activity
from dataall.core.environment.db.models import EnvironmentGroup
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.permissions.db.resource_policy import ResourcePolicy
from dataall.core.permissions.permission_checker import has_resource_permission
from dataall.core.tasks.db.task_models import Task
from dataall.db import utils
from dataall.db.exceptions import UnauthorizedOperation
from dataall.db.models import PrincipalType, ConsumptionRole
from dataall.modules.dataset_sharing.db.enums import ShareObjectActions, ShareableType, ShareItemStatus, \
    ShareObjectStatus
from dataall.modules.dataset_sharing.db.models import ShareObjectItem, ShareObject
from dataall.modules.dataset_sharing.db.share_object_repository import ShareObjectRepository, ShareObjectSM, ShareItemSM
from dataall.modules.dataset_sharing.services.share_exceptions import ShareItemsFound
from dataall.modules.dataset_sharing.services.share_notification_service import ShareNotificationService
from dataall.modules.dataset_sharing.services.share_permissions import REJECT_SHARE_OBJECT, APPROVE_SHARE_OBJECT, \
    SUBMIT_SHARE_OBJECT, SHARE_OBJECT_APPROVER, SHARE_OBJECT_REQUESTER, CREATE_SHARE_OBJECT, DELETE_SHARE_OBJECT, \
    GET_SHARE_OBJECT
from dataall.modules.datasets_base.db.dataset_repository import DatasetRepository
from dataall.modules.datasets_base.db.models import DatasetTable, Dataset
from dataall.modules.datasets_base.services.permissions import DATASET_TABLE_READ


class ShareObjectService:
    @staticmethod
    @has_resource_permission(GET_SHARE_OBJECT)
    def get_share_object(uri):
        with get_context().db_engine.scoped_session() as session:
            return ShareObjectRepository.get_share_by_uri(session, uri)

    @classmethod
    @has_resource_permission(CREATE_SHARE_OBJECT)
    def create_share_object(
            cls,
            uri: str,
            dataset_uri: str,
            item_uri: str,
            item_type: str,
            group_uri,
            principal_id,
            principal_type
    ):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            dataset: Dataset = DatasetRepository.get_dataset_by_uri(session, dataset_uri)
            environment = EnvironmentService.get_environment_by_uri(session, uri)

            if environment.region != dataset.region:
                raise UnauthorizedOperation(
                    action=CREATE_SHARE_OBJECT,
                    message=f'Requester Team {group_uri} works in region {environment.region} '
                            f'and the requested dataset is stored in region {dataset.region}',
                )

            if principal_type == PrincipalType.ConsumptionRole.value:
                consumption_role: ConsumptionRole = EnvironmentService.get_environment_consumption_role(
                    session,
                    principal_id,
                    environment.environmentUri
                )
                principal_iam_role_name = consumption_role.IAMRoleName
            else:
                env_group: EnvironmentGroup = EnvironmentService.get_environment_group(
                    session,
                    group_uri,
                    environment.environmentUri
                )
                principal_iam_role_name = env_group.environmentIAMRoleName

            if (
                    dataset.stewards == group_uri or dataset.SamlAdminGroupName == group_uri
            ) and environment.environmentUri == dataset.environmentUri and principal_type == PrincipalType.Group.value:
                raise UnauthorizedOperation(
                    action=CREATE_SHARE_OBJECT,
                    message=f'Team: {group_uri} is managing the dataset {dataset.name}',
                )

            cls._validate_group_membership(session, group_uri, environment.environmentUri)

            share = ShareObjectRepository.find_share(session, dataset, environment, principal_id, group_uri)
            if not share:
                share = ShareObject(
                    datasetUri=dataset.datasetUri,
                    environmentUri=environment.environmentUri,
                    owner=context.username,
                    groupUri=group_uri,
                    principalId=principal_id,
                    principalType=principal_type,
                    principalIAMRoleName=principal_iam_role_name,
                    status=ShareObjectStatus.Draft.value,
                )
                ShareObjectRepository.save_and_commit(session, share)

            if item_uri:
                item = ShareObjectRepository.get_share_item(session, item_type, item_uri)
                share_item = ShareObjectRepository.find_sharable_item(session, share.shareUri, item_uri)

                s3_access_point_name = utils.slugify(
                    share.datasetUri + '-' + share.principalId,
                    max_length=50, lowercase=True, regex_pattern='[^a-zA-Z0-9-]', separator='-'
                )

                if not share_item and item:
                    new_share_item: ShareObjectItem = ShareObjectItem(
                        shareUri=share.shareUri,
                        itemUri=item_uri,
                        itemType=item_type,
                        itemName=item.name,
                        status=ShareItemStatus.PendingApproval.value,
                        owner=context.username,
                        GlueDatabaseName=dataset.GlueDatabaseName
                        if item_type == ShareableType.Table.value
                        else '',
                        GlueTableName=item.GlueTableName
                        if item_type == ShareableType.Table.value
                        else '',
                        S3AccessPointName=s3_access_point_name
                        if item_type == ShareableType.StorageLocation.value
                        else '',
                    )
                    session.add(new_share_item)

            activity = Activity(
                action='SHARE_OBJECT:CREATE',
                label='SHARE_OBJECT:CREATE',
                owner=context.username,
                summary=f'{context.username} created a share object for the {dataset.name} in {environment.name} for the principal: {principal_id}',
                targetUri=dataset.datasetUri,
                targetType='dataset',
            )
            session.add(activity)

            # Attaching REQUESTER permissions to:
            # requester group (groupUri)
            # dataset.SamlAdminGroupName
            # environment.SamlGroupName
            cls._attach_share_resource_policy(session, share, group_uri)
            cls._attach_share_resource_policy(session, share, dataset.SamlAdminGroupName)
            if dataset.SamlAdminGroupName != environment.SamlGroupName:
                cls._attach_share_resource_policy(session, share, environment.SamlGroupName)

            # Attaching REQUESTER permissions to:
            # dataset.stewards (includes the dataset Admins)
            ResourcePolicy.attach_resource_policy(
                session=session,
                group=dataset.stewards,
                permissions=SHARE_OBJECT_APPROVER,
                resource_uri=share.shareUri,
                resource_type=ShareObject.__name__,
            )
            return share

    @classmethod
    @has_resource_permission(SUBMIT_SHARE_OBJECT)
    def submit_share_object(cls, uri: str):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            share, dataset, states = cls._get_share_data(session, uri)

            valid_states = [ShareItemStatus.PendingApproval.value]
            valid_share_items_states = [x for x in valid_states if x in states]

            if not valid_share_items_states:
                raise ShareItemsFound(
                    action='Submit Share Object',
                    message='The request is empty of pending items. Add items to share request.',
                )

            cls._run_transitions(session, share, states, ShareObjectActions.Submit)
            ShareNotificationService.notify_share_object_submission(
                session, context.username, dataset, share
            )
            return share

    @classmethod
    @has_resource_permission(APPROVE_SHARE_OBJECT)
    def approve_share_object(cls, uri: str):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            share, dataset, states = cls._get_share_data(session, uri)
            cls._run_transitions(session, share, states, ShareObjectActions.Approve)

            # GET TABLES SHARED AND APPROVE SHARE FOR EACH TABLE
            share_table_items = ShareObjectRepository.find_all_share_items(session, uri, ShareableType.Table.value)
            for table in share_table_items:
                ResourcePolicy.attach_resource_policy(
                    session=session,
                    group=share.principalId,
                    permissions=DATASET_TABLE_READ,
                    resource_uri=table.itemUri,
                    resource_type=DatasetTable.__name__,
                )

            ShareNotificationService.notify_share_object_approval(session, context.username, dataset, share)

            approve_share_task: Task = Task(
                action='ecs.share.approve',
                targetUri=uri,
                payload={'environmentUri': share.environmentUri},
            )
            session.add(approve_share_task)

        Worker.queue(engine=context.db_engine, task_ids=[approve_share_task.taskUri])

        return share

    @classmethod
    @has_resource_permission(REJECT_SHARE_OBJECT)
    def reject_share_object(cls, uri: str):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            share, dataset, states = cls._get_share_data(session, uri)
            cls._run_transitions(session, share, states, ShareObjectActions.Reject)
            ResourcePolicy.delete_resource_policy(
                session=session,
                group=share.groupUri,
                resource_uri=dataset.datasetUri,
            )

            ShareNotificationService.notify_share_object_rejection(session, context.username, dataset, share)
            return share

    @classmethod
    @has_resource_permission(DELETE_SHARE_OBJECT)
    def delete_share_object(cls, uri: str):
        with get_context().db_engine.scoped_session() as session:
            share, dataset, states = cls._get_share_data(session, uri)
            shared_share_items_states = [x for x in ShareItemSM.get_share_item_shared_states() if x in states]

            new_state = cls._run_transitions(session, share, states, ShareObjectActions.Delete)
            if shared_share_items_states:
                raise ShareItemsFound(
                    action='Delete share object',
                    message='There are shared items in this request. '
                            'Revoke access to these items before deleting the request.',
                )

            if new_state == ShareObjectStatus.Deleted.value:
                session.delete(share)

            return True

    @staticmethod
    def resolve_share_object_statistics(uri):
        with get_context().db_engine.scoped_session() as session:
            tables = ShareObjectRepository.count_sharable_items(session, uri, 'DatasetTable')
            locations = ShareObjectRepository.count_sharable_items(session, uri, 'DatasetStorageLocation')
            shared_items = ShareObjectRepository.count_items_in_states(
                session, uri, ShareItemSM.get_share_item_shared_states()
            )
            revoked_items = ShareObjectRepository.count_items_in_states(
                session, uri, [ShareItemStatus.Revoke_Succeeded.value]
            )
            failed_states = [
                ShareItemStatus.Share_Failed.value,
                ShareItemStatus.Revoke_Failed.value
            ]
            failed_items = ShareObjectRepository.count_items_in_states(
                session, uri, failed_states
            )
            pending_items = ShareObjectRepository.count_items_in_states(
                session, uri, [ShareItemStatus.PendingApproval.value]
            )
            return {'tables': tables, 'locations': locations, 'sharedItems': shared_items, 'revokedItems': revoked_items,
                    'failedItems': failed_items, 'pendingItems': pending_items}

    @staticmethod
    def list_shares_in_my_inbox(filter: dict):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            return ShareObjectRepository.list_user_received_share_requests(
                session=session,
                username=context.username,
                groups=context.groups,
                data=filter,
            )

    @staticmethod
    def list_shares_in_my_outbox(filter):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            return ShareObjectRepository.list_user_sent_share_requests(
                session=session,
                username=context.username,
                groups=context.groups,
                data=filter,
            )

    @staticmethod
    def _run_transitions(session, share, share_items_states, action):
        share_sm = ShareObjectSM(share.status)
        new_share_state = share_sm.run_transition(action.value)

        for item_state in share_items_states:
            item_sm = ShareItemSM(item_state)
            new_state = item_sm.run_transition(action.value)
            item_sm.update_state(session, share.shareUri, new_state)

        share_sm.update_state(session, share, new_share_state)
        return new_share_state

    @staticmethod
    def _get_share_data(session, uri):
        share = ShareObjectRepository.get_share_by_uri(session, uri)
        dataset = DatasetRepository.get_dataset_by_uri(session, share.datasetUri)
        share_items_states = ShareObjectRepository.get_share_items_states(session, uri)
        return share, dataset, share_items_states

    @staticmethod
    def _attach_share_resource_policy(session, share, group):
        ResourcePolicy.attach_resource_policy(
            session=session,
            group=group,
            permissions=SHARE_OBJECT_REQUESTER,
            resource_uri=share.shareUri,
            resource_type=ShareObject.__name__,
        )

    @staticmethod
    def _validate_group_membership(
        session, share_object_group, environment_uri
    ):
        context = get_context()
        if share_object_group and share_object_group not in context.groups:
            raise UnauthorizedOperation(
                action=CREATE_SHARE_OBJECT,
                message=f'User: {context.username} is not a member of the team {share_object_group}',
            )
        if share_object_group not in EnvironmentService.list_environment_groups(
            session=session,
            uri=environment_uri,
        ):
            raise UnauthorizedOperation(
                action=CREATE_SHARE_OBJECT,
                message=f'Team: {share_object_group} is not a member of the environment {environment_uri}',
            )
