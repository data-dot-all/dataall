import logging

from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.core.tasks.service_handlers import Worker
from dataall.base.context import get_context
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.tasks.db.task_models import Task
from dataall.base.db import utils
from dataall.base.db.exceptions import ObjectNotFound, UnauthorizedOperation
from dataall.modules.dataset_sharing.services.dataset_sharing_enums import (
    ShareObjectActions,
    ShareableType,
    ShareItemStatus,
    ShareItemActions,
    ShareItemHealthStatus,
    PrincipalType,
)
from dataall.modules.dataset_sharing.aws.glue_client import GlueClient
from dataall.modules.dataset_sharing.db.share_object_models import ShareObjectItem
from dataall.modules.dataset_sharing.db.share_object_repositories import (
    ShareObjectRepository,
    ShareObjectSM,
    ShareItemSM,
)
from dataall.modules.dataset_sharing.services.share_exceptions import ShareItemsFound
from dataall.modules.dataset_sharing.services.share_notification_service import ShareNotificationService
from dataall.modules.dataset_sharing.services.share_permissions import (
    GET_SHARE_OBJECT,
    ADD_ITEM,
    REMOVE_ITEM,
    LIST_ENVIRONMENT_SHARED_WITH_OBJECTS,
    APPROVE_SHARE_OBJECT,
)
from dataall.modules.datasets_base.db.dataset_repositories import DatasetRepository
from dataall.modules.datasets_base.db.dataset_models import Dataset

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
            dataset = DatasetRepository.get_dataset_by_uri(session, share.datasetUri)
            revoked_items_states = ShareObjectRepository.get_share_items_states(session, uri, revoked_uris)
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

            if share.groupUri != dataset.SamlAdminGroupName and share.principalType == PrincipalType.Group.value:
                log.info('Deleting TABLE/FOLDER READ permissions...')
                ShareItemService._delete_dataset_table_read_permission(session, share)
                ShareItemService._delete_dataset_folder_read_permission(session, share)

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
            dataset: Dataset = DatasetRepository.get_dataset_by_uri(session, share.datasetUri)
            target_environment = EnvironmentService.get_environment_by_uri(session, share.environmentUri)

            share_sm = ShareObjectSM(share.status)
            new_share_state = share_sm.run_transition(ShareItemActions.AddItem.value)
            share_sm.update_state(session, share, new_share_state)

            item = ShareObjectRepository.get_share_item(session, item_type, item_uri)
            if not item:
                raise ObjectNotFound('ShareObjectItem', item_uri)

            if item_type == ShareableType.Table.value and item.region != target_environment.region:
                raise UnauthorizedOperation(
                    action=ADD_ITEM,
                    message=f'Lake Formation cross region sharing is not supported. '
                    f'Table {item.GlueTableName} is in {item.region} and target environment '
                    f'{target_environment.name} is in {target_environment.region} ',
                )

            share_item: ShareObjectItem = ShareObjectRepository.find_sharable_item(session, uri, item_uri)

            s3_access_point_name = utils.slugify(
                share.datasetUri + '-' + share.principalId,
                max_length=50,
                lowercase=True,
                regex_pattern='[^a-zA-Z0-9-]',
                separator='-',
            )
            log.info(f'S3AccessPointName={s3_access_point_name}')

            if not share_item:
                share_item = ShareObjectItem(
                    shareUri=uri,
                    itemUri=item_uri,
                    itemType=item_type,
                    itemName=item.name,
                    status=ShareItemStatus.PendingApproval.value,
                    owner=context.username,
                    GlueDatabaseName=ShareItemService._get_glue_database_for_share(
                        dataset.GlueDatabaseName, dataset.AwsAccountId, dataset.region
                    )
                    if item_type == ShareableType.Table.value
                    else '',
                    GlueTableName=item.GlueTableName if item_type == ShareableType.Table.value else '',
                    S3AccessPointName=s3_access_point_name if item_type == ShareableType.StorageLocation.value else '',
                )
                session.add(share_item)
        return share_item

    @staticmethod
    @ResourcePolicyService.has_resource_permission(REMOVE_ITEM, parent_resource=_get_share_uri)
    def remove_shared_item(uri: str):
        with get_context().db_engine.scoped_session() as session:
            share_item = ShareObjectRepository.get_share_item_by_uri(session, uri)
            if (
                share_item.itemType == ShareableType.Table.value
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
            return ShareObjectRepository.get_share_item(session, item.itemType, item.itemUri)

    @staticmethod
    def check_existing_shared_items(share):
        with get_context().db_engine.scoped_session() as session:
            return ShareObjectRepository.check_existing_shared_items(session, share.shareUri)

    @staticmethod
    def list_shareable_objects(share, filter, is_revokable=False):
        states = None
        if is_revokable:
            states = ShareItemSM.get_share_item_revokable_states()

        with get_context().db_engine.scoped_session() as session:
            return ShareObjectRepository.list_shareable_items(session, share, states, filter)

    @staticmethod
    @ResourcePolicyService.has_resource_permission(LIST_ENVIRONMENT_SHARED_WITH_OBJECTS)
    def paginated_shared_with_environment_datasets(session, uri, data) -> dict:
        return ShareObjectRepository.paginate_shared_datasets(session, uri, data)

    @staticmethod
    def _get_glue_database_for_share(glueDatabase, account_id, region):
        # Check if a catalog account exists and return database accordingly
        try:
            catalog_dict = GlueClient(
                account_id=account_id,
                region=region,
                database=glueDatabase,
            ).get_source_catalog()

            if catalog_dict is not None:
                return catalog_dict.get('database_name')
            else:
                return glueDatabase
        except Exception as e:
            raise e

    @staticmethod
    def _delete_dataset_table_read_permission(session, share):
        """
        Delete Table permissions to share groups
        """
        share_table_items = ShareObjectRepository.find_all_share_items(
            session, share.shareUri, ShareableType.Table.value, [ShareItemStatus.Revoke_Approved.value]
        )
        for table in share_table_items:
            ResourcePolicyService.delete_resource_policy(
                session=session, group=share.groupUri, resource_uri=table.itemUri
            )

    @staticmethod
    def _delete_dataset_folder_read_permission(session, share):
        """
        Delete Folder permissions to share groups
        """
        share_folder_items = ShareObjectRepository.find_all_share_items(
            session, share.shareUri, ShareableType.StorageLocation.value, [ShareItemStatus.Revoke_Approved.value]
        )
        for location in share_folder_items:
            ResourcePolicyService.delete_resource_policy(
                session=session,
                group=share.groupUri,
                resource_uri=location.itemUri,
            )
