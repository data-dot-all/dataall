import logging

from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyService
from dataall.core.tasks.service_handlers import Worker
from dataall.base.context import get_context
from dataall.core.tasks.db.task_models import Task
from dataall.base.db.exceptions import ObjectNotFound, UnauthorizedOperation, InvalidInput
from dataall.modules.shares_base.services.shares_enums import (
    ShareObjectActions,
    ShareItemStatus,
    ShareItemActions,
    ShareItemHealthStatus,
    ShareableType,
)
from dataall.modules.shares_base.db.share_object_models import ShareObjectItem
from dataall.modules.shares_base.db.share_object_repositories import ShareObjectRepository
from dataall.modules.shares_base.db.share_state_machines_repositories import ShareStatusRepository
from dataall.modules.shares_base.db.share_object_item_repositories import ShareObjectItemRepository
from dataall.modules.shares_base.db.share_object_state_machines import (
    ShareObjectSM,
    ShareItemSM,
)
from sqlalchemy import exc
from dataall.modules.shares_base.services.share_exceptions import ShareItemsFound
from dataall.modules.shares_base.services.share_notification_service import ShareNotificationService
from dataall.modules.shares_base.services.share_permissions import (
    GET_SHARE_OBJECT,
    ADD_ITEM,
    REMOVE_ITEM,
    LIST_ENVIRONMENT_SHARED_WITH_OBJECTS,
    APPROVE_SHARE_OBJECT,
    MANAGE_SHARES,
)
from dataall.modules.shares_base.services.share_processor_manager import ShareProcessorManager
from dataall.modules.datasets_base.db.dataset_repositories import DatasetBaseRepository

log = logging.getLogger(__name__)


class ShareItemService:
    @staticmethod
    def _get_share_uri(session, uri):
        share_item = ShareObjectRepository.get_share_item_by_uri(session, uri)
        return share_item.shareUri

    @staticmethod
    def _get_share_uri_from_item_filter_uri(session, uri):
        share_item = ShareObjectItemRepository.get_share_item_by_item_filter_uri(session, uri)
        return share_item.shareUri

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_SHARES)
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
    @TenantPolicyService.has_tenant_permission(MANAGE_SHARES)
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
    @TenantPolicyService.has_tenant_permission(MANAGE_SHARES)
    @ResourcePolicyService.has_resource_permission(GET_SHARE_OBJECT)
    def revoke_items_share_object(uri, revoked_uris):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            share = ShareObjectRepository.get_share_by_uri(session, uri)
            dataset = DatasetBaseRepository.get_dataset_by_uri(session, share.datasetUri)
            revoked_items_states = ShareStatusRepository.get_share_items_states(session, uri, revoked_uris)
            revoked_items_health_states = ShareStatusRepository.get_share_items_health_states(
                session, uri, revoked_uris
            )
            revoked_items = [ShareObjectRepository.get_share_item_by_uri(session, uri) for uri in revoked_uris]

            if not revoked_items_states:
                raise ShareItemsFound(
                    action='Revoke Items from Share Object',
                    message='Nothing to be revoked.',
                )

            if ShareItemHealthStatus.PendingReApply.value in revoked_items_health_states:
                raise UnauthorizedOperation(
                    action='Revoke Items from Share Object',
                    message='Cannot revoke while reapply pending for one or more items.',
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
    @TenantPolicyService.has_tenant_permission(MANAGE_SHARES)
    @ResourcePolicyService.has_resource_permission(ADD_ITEM)
    def add_shared_item(uri: str, data: dict = None):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            item_type = data.get('itemType')
            item_uri = data.get('itemUri')
            share = ShareObjectRepository.get_share_by_uri(session, uri)

            share_sm = ShareObjectSM(share.status)
            new_share_state = share_sm.run_transition(ShareItemActions.AddItem.value)
            share_sm.update_state(session, share, new_share_state)

            processor = ShareProcessorManager.get_processor_by_item_type(item_type)
            item = ShareObjectRepository.get_share_item_details(session, processor.shareable_type, item_uri)
            if not item:
                raise ObjectNotFound('ShareObjectItem', item_uri)

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
    @TenantPolicyService.has_tenant_permission(MANAGE_SHARES)
    @ResourcePolicyService.has_resource_permission(REMOVE_ITEM, parent_resource=_get_share_uri)
    def remove_shared_item(uri: str):
        with get_context().db_engine.scoped_session() as session:
            share_item = ShareObjectRepository.get_share_item_by_uri(session, uri)
            item_sm = ShareItemSM(share_item.status)
            item_sm.run_transition(ShareItemActions.RemoveItem.value)
            ShareObjectRepository.remove_share_object_item(session, share_item)
            if share_item.attachedDataFilterUri:
                share_item_filter = ShareObjectItemRepository.get_share_item_filter_by_uri(
                    session, share_item.attachedDataFilterUri
                )
                ShareObjectItemRepository.delete_share_item_filter(session, share_item_filter)
        return True

    @staticmethod
    @ResourcePolicyService.has_resource_permission(GET_SHARE_OBJECT)
    def resolve_shared_item(uri, item: ShareObjectItem):
        with get_context().db_engine.scoped_session() as session:
            processor = ShareProcessorManager.get_processor_by_item_type(item.itemType)
            return ShareObjectRepository.get_share_item_details(session, processor.shareable_type, item.itemUri)

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
    def paginated_shared_with_environment_datasets(uri, data) -> dict:
        context = get_context()
        with context.db_engine.scoped_session() as session:
            share_item_shared_states = ShareStatusRepository.get_share_item_shared_states()
            return ShareObjectRepository.paginate_shared_datasets(session, uri, data, share_item_shared_states)

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_SHARES)
    @ResourcePolicyService.has_resource_permission(APPROVE_SHARE_OBJECT, parent_resource=_get_share_uri)
    def update_filters_table_share_item(uri: str, data: dict):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            if share_item := ShareObjectRepository.get_share_item_by_uri(session, uri):
                if share_item.itemType != ShareableType.Table.value:
                    raise Exception(f'Share item is not type {ShareableType.Table.value} - required for data filters')

                if share_item.status in ShareStatusRepository.get_share_item_shared_states():
                    raise Exception(f'Share item already shared in state {share_item.status} - can not assign filters')
                try:
                    if share_item.attachedDataFilterUri:
                        share_item_filter = ShareObjectItemRepository.get_share_item_filter_by_uri(
                            session, share_item.attachedDataFilterUri
                        )
                        ShareObjectItemRepository.update_share_item_filter(session, share_item_filter, data)
                        return True

                    share_item_filter = ShareObjectItemRepository.create_share_item_filter(session, share_item, data)
                    share_item.attachedDataFilterUri = share_item_filter.attachedDataFilterUri
                    return True
                except exc.IntegrityError:
                    raise InvalidInput(
                        'label',
                        data.get('label'),
                        f'same label already exists on another share item for table {share_item.itemName}',
                    )
            raise ObjectNotFound('ShareObjectItem', uri)

    @staticmethod
    @ResourcePolicyService.has_resource_permission(
        GET_SHARE_OBJECT, parent_resource=_get_share_uri_from_item_filter_uri
    )
    def get_share_item_data_filters(uri: str):
        with get_context().db_engine.scoped_session() as session:
            return ShareObjectItemRepository.get_share_item_filter_by_uri(session, uri)

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_SHARES)
    @ResourcePolicyService.has_resource_permission(
        APPROVE_SHARE_OBJECT, parent_resource=_get_share_uri_from_item_filter_uri
    )
    def remove_share_item_data_filters(uri: str):
        with get_context().db_engine.scoped_session() as session:
            share_item = ShareObjectItemRepository.get_share_item_by_item_filter_uri(session, uri)
            if share_item.status in ShareStatusRepository.get_share_item_shared_states():
                raise Exception(
                    f'Share item in shared state {share_item.status} - can not remove filters, must revoke first...'
                )
            share_item.attachedDataFilterUri = None
            item_data_filter = ShareObjectItemRepository.get_share_item_filter_by_uri(session, uri)
            return ShareObjectItemRepository.delete_share_item_filter(session, item_data_filter)
