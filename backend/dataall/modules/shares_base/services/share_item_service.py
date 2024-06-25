import logging

from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.core.stacks.aws.ecs import Ecs
from dataall.core.tasks.service_handlers import Worker
from dataall.base.context import get_context
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.tasks.db.task_models import Task
from dataall.base.db.exceptions import ObjectNotFound, UnauthorizedOperation
from dataall.modules.shares_base.services.shares_enums import (
    ShareObjectActions,
    ShareableType,
    ShareItemStatus,
    ShareItemActions,
    ShareItemHealthStatus,
)
from dataall.modules.shares_base.db.share_object_models import ShareObjectItem
from dataall.modules.shares_base.db.share_object_repositories import ShareObjectRepository
from dataall.modules.shares_base.db.share_state_machines_repositories import ShareStatusRepository
from dataall.modules.shares_base.db.share_object_state_machines import (
    ShareObjectSM,
    ShareItemSM,
)
from dataall.modules.shares_base.services.share_exceptions import ShareItemsFound
from dataall.modules.shares_base.services.share_notification_service import ShareNotificationService
from dataall.modules.shares_base.services.share_permissions import (
    GET_SHARE_OBJECT,
    ADD_ITEM,
    REMOVE_ITEM,
    LIST_ENVIRONMENT_SHARED_WITH_OBJECTS,
    APPROVE_SHARE_OBJECT,
)
from dataall.modules.shares_base.services.share_processor_manager import ShareProcessorManager
from dataall.modules.datasets_base.db.dataset_repositories import DatasetBaseRepository

log = logging.getLogger(__name__)


class ShareItemService:
    @staticmethod
    def _get_share_uri(session, uri):
        share_item = ShareObjectRepository.get_share_item_by_uri(session, uri)
        share = ShareObjectRepository.get_share_by_uri(session, share_item.shareUri)
        return share.shareUri

    @staticmethod
    @ResourcePolicyService.has_resource_permission(GET_SHARE_OBJECT)
    def verify_items_share_object(uri, item_uris):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            verify_items = [ShareObjectRepository.get_share_item_by_uri(session, uri) for uri in item_uris]
            for item in verify_items:
                setattr(item, 'healthStatus', ShareItemHealthStatus.PendingVerify.value)

            verify_share_items_task: Task = Task(action='ecs.share.verify', targetUri=uri)
            session.add(verify_share_items_task)

        Worker.queue(engine=context.db_engine, task_ids=[verify_share_items_task.taskUri])
        return True

    @staticmethod
    @ResourcePolicyService.has_resource_permission(APPROVE_SHARE_OBJECT)
    def reapply_items_share_object(uri, item_uris):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            verify_items = [ShareObjectRepository.get_share_item_by_uri(session, uri) for uri in item_uris]
            for item in verify_items:
                setattr(item, 'healthStatus', ShareItemHealthStatus.PendingReApply.value)

            reapply_share_items_task: Task = Task(action='ecs.share.reapply', targetUri=uri)
            session.add(reapply_share_items_task)

        Worker.queue(engine=context.db_engine, task_ids=[reapply_share_items_task.taskUri])
        return True

    @staticmethod
    @ResourcePolicyService.has_resource_permission(GET_SHARE_OBJECT)
    def revoke_items_share_object(uri, revoked_uris):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            share = ShareObjectRepository.get_share_by_uri(session, uri)
            dataset = DatasetBaseRepository.get_dataset_by_uri(session, share.datasetUri)
            revoked_items_states = ShareStatusRepository.get_share_items_states(session, uri, revoked_uris)
            revoked_items = [ShareObjectRepository.get_share_item_by_uri(session, uri) for uri in revoked_uris]

            if not revoked_items_states:
                raise ShareItemsFound(
                    action='Revoke Items from Share Object',
                    message='Nothing to be revoked.',
                )

            share_sm = ShareObjectSM(share.status)
            new_share_state = share_sm.run_transition(ShareObjectActions.RevokeItems.value)

            for item_state in revoked_items_states:
                item_sm = ShareItemSM(item_state)
                new_state = item_sm.run_transition(ShareObjectActions.RevokeItems.value)
                for item in revoked_items:
                    if item.status == item_state:
                        item_sm.update_state_single_item(session, item, new_state)

            share_sm.update_state(session, share, new_share_state)

            ShareNotificationService(session=session, dataset=dataset, share=share).notify_share_object_rejection(
                email_id=context.username
            )

            revoke_share_task: Task = Task(
                action='ecs.share.revoke',
                targetUri=uri,
                payload={'environmentUri': share.environmentUri},
            )
            session.add(revoke_share_task)

        Worker.queue(engine=context.db_engine, task_ids=[revoke_share_task.taskUri])

        return share

    @staticmethod
    @ResourcePolicyService.has_resource_permission(ADD_ITEM)
    def add_shared_item(uri: str, data: dict = None):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            item_type = data.get('itemType')
            item_uri = data.get('itemUri')
            share = ShareObjectRepository.get_share_by_uri(session, uri)
            target_environment = EnvironmentService.get_environment_by_uri(session, share.environmentUri)

            share_sm = ShareObjectSM(share.status)
            new_share_state = share_sm.run_transition(ShareItemActions.AddItem.value)
            share_sm.update_state(session, share, new_share_state)
            processor = ShareProcessorManager.get_processor_by_item_type(item_type)
            item = ShareObjectRepository.get_share_item_details(session, processor.shareable_type, item_uri)
            if not item:
                raise ObjectNotFound('ShareObjectItem', item_uri)

            if (
                item_type == ShareableType.Table.value and item.region != target_environment.region
            ):  # TODO Part10: remove from here (we might be able to remove get_share_item_details entirely
                raise UnauthorizedOperation(
                    action=ADD_ITEM,
                    message=f'Lake Formation cross region sharing is not supported. '
                    f'Table {item.itemUri} is in {item.region} and target environment '
                    f'{target_environment.name} is in {target_environment.region} ',
                )

            share_item: ShareObjectItem = ShareObjectRepository.find_sharable_item(session, uri, item_uri)

            if not share_item:
                share_item = ShareObjectItem(
                    shareUri=uri,
                    itemUri=item_uri,
                    itemType=item_type,
                    itemName=item.name,
                    status=ShareItemStatus.PendingApproval.value,
                    owner=context.username,
                )
                session.add(share_item)
        return share_item

    @staticmethod
    @ResourcePolicyService.has_resource_permission(REMOVE_ITEM, parent_resource=_get_share_uri)
    def remove_shared_item(uri: str):
        with get_context().db_engine.scoped_session() as session:
            share_item = ShareObjectRepository.get_share_item_by_uri(session, uri)
            if (
                share_item.itemType == ShareableType.Table.value  # TODO Part10 - REMOVE
                and share_item.status == ShareItemStatus.Share_Failed.value
            ):
                share = ShareObjectRepository.get_share_by_uri(session, share_item.shareUri)
                ResourcePolicyService.delete_resource_policy(
                    session=session,
                    group=share.groupUri,
                    resource_uri=share_item.itemUri,
                )

            item_sm = ShareItemSM(share_item.status)
            item_sm.run_transition(ShareItemActions.RemoveItem.value)
            ShareObjectRepository.remove_share_object_item(session, share_item)
        return True

    @staticmethod
    @ResourcePolicyService.has_resource_permission(GET_SHARE_OBJECT)
    def resolve_shared_item(uri, item: ShareObjectItem):
        with get_context().db_engine.scoped_session() as session:
            processor = ShareProcessorManager.get_processor_by_item_type(item.itemType)
            return ShareObjectRepository.get_share_item_details(
                session, processor.shareable_type, item.itemUri
            )  # TODO - check it works

    @staticmethod
    def check_existing_shared_items(share):
        with get_context().db_engine.scoped_session() as session:
            return ShareStatusRepository.check_existing_shared_items(session, share.shareUri)

    @staticmethod
    def list_shareable_objects(share, filter, is_revokable=False):
        status = None
        if is_revokable:
            status = ShareStatusRepository.get_share_item_revokable_states()

        with get_context().db_engine.scoped_session() as session:
            subqueries = []
            for type, processor in ShareProcessorManager.SHARING_PROCESSORS.items():
                subqueries.append(
                    ShareObjectRepository.list_shareable_items_of_type(
                        session=session,
                        share=share,
                        type=type,
                        share_type_model=processor.shareable_type,
                        share_type_uri=processor.shareable_uri,
                        status=status,
                    )
                )
            return ShareObjectRepository.paginated_list_shareable_items(
                session=session, subqueries=subqueries, data=filter
            )

    @staticmethod
    @ResourcePolicyService.has_resource_permission(LIST_ENVIRONMENT_SHARED_WITH_OBJECTS)
    def paginated_shared_with_environment_datasets(session, uri, data) -> dict:
        share_item_shared_states = ShareStatusRepository.get_share_item_shared_states()
        return ShareObjectRepository.paginate_shared_datasets(session, uri, data, share_item_shared_states)
