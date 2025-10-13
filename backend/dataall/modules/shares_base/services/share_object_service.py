from datetime import datetime

from dataall.base.utils.expiration_util import ExpirationUtils
import logging
from abc import ABC, abstractmethod
from typing import Dict, List

from dataall.base.context import get_context
from dataall.base.db.exceptions import UnauthorizedOperation, InvalidInput
from dataall.core.activity.db.activity_models import Activity
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyService
from dataall.core.environment.db.environment_models import EnvironmentGroup, ConsumptionRole
from dataall.core.tasks.db.task_models import Task
from dataall.core.tasks.service_handlers import Worker
from dataall.modules.datasets_base.db.dataset_models import DatasetBase
from dataall.modules.datasets_base.db.dataset_repositories import DatasetBaseRepository
from dataall.modules.datasets_base.services.datasets_enums import DatasetTypes
from dataall.modules.shares_base.db.share_object_models import ShareObjectItem, ShareObject
from dataall.modules.shares_base.db.share_object_repositories import ShareObjectRepository
from dataall.modules.shares_base.db.share_object_state_machines import (
    ShareObjectSM,
    ShareItemSM,
)
from dataall.modules.shares_base.db.share_state_machines_repositories import ShareStatusRepository
from dataall.modules.shares_base.services.share_exceptions import ShareItemsFound
from dataall.modules.shares_base.services.share_notification_service import ShareNotificationService
from dataall.modules.shares_base.services.share_permissions import (
    REJECT_SHARE_OBJECT,
    APPROVE_SHARE_OBJECT,
    SUBMIT_SHARE_OBJECT,
    SHARE_OBJECT_APPROVER,
    SHARE_OBJECT_REQUESTER,
    CREATE_SHARE_OBJECT,
    DELETE_SHARE_OBJECT,
    GET_SHARE_OBJECT,
    MANAGE_SHARES,
)
from dataall.modules.shares_base.services.share_processor_manager import ShareProcessorManager
from dataall.modules.shares_base.services.shares_enums import (
    ShareObjectActions,
    ShareItemStatus,
    ShareObjectStatus,
    PrincipalType,
)

log = logging.getLogger(__name__)


class SharesValidatorInterface(ABC):
    @staticmethod
    @abstractmethod
    def validate_share_object_create(
        session,
        dataset,
        group_uri,
        environment,
        principal_type,
        principal_id,
        principal_role_name,
        attachMissingPolicies,
        permissions,
    ) -> bool:
        """Executes checks when a share request is created"""
        ...

    @staticmethod
    @abstractmethod
    def validate_share_object_submit(session, dataset, share) -> bool:
        """Executes checks when a share item is submitted"""
        ...

    @staticmethod
    @abstractmethod
    def validate_share_object_approve(session, dataset, share) -> bool:
        """Executes checks when a share item is approved"""
        ...


class ShareObjectService:
    SHARING_VALIDATORS: Dict[DatasetTypes, SharesValidatorInterface] = {}

    @classmethod
    def register_validator(cls, dataset_type: DatasetTypes, validator) -> None:
        cls.SHARING_VALIDATORS[dataset_type] = validator

    @classmethod
    def validate_share_object(
        cls, share_action: ShareObjectActions, dataset_type: DatasetTypes, session, dataset, *args, **kwargs
    ):
        log.info(f'Validating share object {share_action.value} for {dataset_type.value=}')
        for ds_type, validator in cls.SHARING_VALIDATORS.items():
            if ds_type.value == dataset_type.value:
                if share_action.value == ShareObjectActions.Create.value:
                    validator.validate_share_object_create(session, dataset, *args, **kwargs)
                elif share_action.value == ShareObjectActions.Submit.value:
                    validator.validate_share_object_submit(session, dataset, *args, **kwargs)
                elif share_action.value == ShareObjectActions.Approve.value:
                    validator.validate_share_object_approve(session, dataset, *args, **kwargs)
                else:
                    raise ValueError(f'Invalid share action {share_action.value}')

    @staticmethod
    @ResourcePolicyService.has_resource_permission(GET_SHARE_OBJECT)
    def get_share_object(uri):
        with get_context().db_engine.scoped_session() as session:
            return ShareObjectRepository.get_share_by_uri(session, uri)

    @classmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_SHARES)
    @ResourcePolicyService.has_resource_permission(CREATE_SHARE_OBJECT)
    def create_share_object(
        cls,
        uri: str,
        dataset_uri: str,
        item_uri: str,
        item_type: str,
        group_uri,
        principal_id,
        principal_role_name,
        principal_type,
        requestPurpose,
        attachMissingPolicies,
        permissions: List[str],
        shareExpirationPeriod,
        nonExpirable: bool = False,
    ):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            dataset: DatasetBase = DatasetBaseRepository.get_dataset_by_uri(session, dataset_uri)
            environment = EnvironmentService.get_environment_by_uri(session, uri)

            cls._validate_group_membership(session, group_uri, environment.environmentUri)

            principal_role_name = cls._resolve_principal_role_name(
                session, group_uri, environment.environmentUri, principal_id, principal_role_name, principal_type
            )

            cls.validate_share_object(
                share_action=ShareObjectActions.Create,
                dataset_type=dataset.datasetType,
                session=session,
                dataset=dataset,
                environment=environment,
                group_uri=group_uri,
                principal_id=principal_id,
                principal_role_name=principal_role_name,
                principal_type=principal_type,
                attachMissingPolicies=attachMissingPolicies,
                permissions=permissions,
            )

            share = ShareObjectRepository.find_share(
                session=session,
                dataset=dataset,
                env=environment,
                principal_id=principal_id,
                principal_role_name=principal_role_name,
                group_uri=group_uri,
            )
            already_existed = share is not None

            if (
                dataset.enableExpiration
                and not nonExpirable
                and (
                    shareExpirationPeriod > dataset.expiryMaxDuration
                    or shareExpirationPeriod < dataset.expiryMinDuration
                )
            ):
                raise Exception('Share expiration period is not within the maximum and the minimum expiration duration')

            shareExpiryDate = None
            if nonExpirable:
                shareExpiryDate = None
                shareExpirationPeriod = None
            elif dataset.enableExpiration:
                shareExpiryDate = ExpirationUtils.calculate_expiry_date(shareExpirationPeriod, dataset.expirySetting)

            if not share:
                share = ShareObject(
                    datasetUri=dataset.datasetUri,
                    environmentUri=environment.environmentUri,
                    owner=context.username,
                    groupUri=group_uri,
                    principalId=principal_id,
                    principalType=principal_type,
                    principalRoleName=principal_role_name,
                    status=ShareObjectStatus.Draft.value,
                    requestPurpose=requestPurpose,
                    permissions=permissions,
                    requestedExpiryDate=shareExpiryDate,
                    nonExpirable=nonExpirable,
                    shareExpirationPeriod=shareExpirationPeriod,
                )
                ShareObjectRepository.save_and_commit(session, share)

            if item_uri:
                processor = ShareProcessorManager.get_processor_by_item_type(item_type)

                item = ShareObjectRepository.get_share_item_details(session, processor.shareable_type, item_uri)
                share_item = ShareObjectRepository.find_sharable_item(session, share.shareUri, item_uri)

                if not share_item and item:
                    new_share_item: ShareObjectItem = ShareObjectItem(
                        shareUri=share.shareUri,
                        itemUri=item_uri,
                        itemType=item_type,
                        itemName=item.name,
                        status=ShareItemStatus.PendingApproval.value,
                        owner=context.username,
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
            # environment.SamlGroupName (if not dataset admins)
            ResourcePolicyService.attach_resource_policy(
                session=session,
                group=group_uri,
                permissions=SHARE_OBJECT_REQUESTER,
                resource_uri=share.shareUri,
                resource_type=ShareObject.__name__,
            )

            # Attaching APPROVER permissions to:
            # dataset.stewards (includes the dataset Admins)
            ResourcePolicyService.attach_resource_policy(
                session=session,
                group=dataset.SamlAdminGroupName,
                permissions=SHARE_OBJECT_APPROVER,
                resource_uri=share.shareUri,
                resource_type=ShareObject.__name__,
            )
            if dataset.stewards != dataset.SamlAdminGroupName:
                ResourcePolicyService.attach_resource_policy(
                    session=session,
                    group=dataset.stewards,
                    permissions=SHARE_OBJECT_APPROVER,
                    resource_uri=share.shareUri,
                    resource_type=ShareObject.__name__,
                )
            share.alreadyExisted = already_existed
            return share

    @classmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_SHARES)
    @ResourcePolicyService.has_resource_permission(SUBMIT_SHARE_OBJECT)
    def submit_share_object(cls, uri: str):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            share, dataset, states = cls._get_share_data(session, uri)

            cls.validate_share_object(
                share_action=ShareObjectActions.Submit,
                dataset_type=dataset.datasetType,
                session=session,
                dataset=dataset,
                share=share,
            )

            valid_states = [ShareItemStatus.PendingApproval.value]
            valid_share_items_states = [x for x in valid_states if x in states]

            if not valid_share_items_states:
                raise ShareItemsFound(
                    action='Submit Share Object',
                    message='The request is empty of pending items. Add items to share request.',
                )

            cls._run_transitions(session, share, states, ShareObjectActions.Submit)

            ShareNotificationService(session=session, dataset=dataset, share=share).notify_share_object_submission(
                email_id=context.username
            )

            # if parent dataset has auto-approve flag, we trigger the next transition to approved state
            if dataset.autoApprovalEnabled:
                ResourcePolicyService.attach_resource_policy(
                    session=session,
                    group=share.groupUri,
                    permissions=SHARE_OBJECT_APPROVER,
                    resource_uri=share.shareUri,
                    resource_type=ShareObject.__name__,
                )
                share = cls.approve_share_object(uri=share.shareUri)

            return share

    @classmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_SHARES)
    @ResourcePolicyService.has_resource_permission(SUBMIT_SHARE_OBJECT)
    def submit_share_extension(cls, uri: str, expiration: int, extension_reason: str, nonExpirable: bool):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            share, dataset, states = cls._get_share_data(session, uri)
            if dataset.enableExpiration:
                if nonExpirable is False and expiration is None:
                    raise InvalidInput(
                        param_name='Share Expiration',
                        param_value='',
                        constraint='period not provided. Either make your share non-expiring or provide a expiration period',
                    )

                if not nonExpirable and (
                    expiration < dataset.expiryMinDuration or expiration > dataset.expiryMaxDuration
                ):
                    raise InvalidInput(
                        param_name='Share Expiration',
                        param_value=expiration,
                        constraint=f'between {dataset.expiryMinDuration} and {dataset.expiryMaxDuration}',
                    )

                cls._run_transitions(session, share, states, ShareObjectActions.Extension)

                if nonExpirable:
                    share.nonExpirable = True
                    share.requestedExpiryDate = None
                    share.shareExpirationPeriod = None
                else:
                    expiration_date = ExpirationUtils.calculate_expiry_date(expiration, dataset.expirySetting)
                    share.requestedExpiryDate = expiration_date
                    share.shareExpirationPeriod = expiration

                share.extensionReason = extension_reason
                share.submittedForExtension = True

                ShareNotificationService(
                    session=session, dataset=dataset, share=share
                ).notify_share_object_extension_submission(email_id=context.username)

                if dataset.autoApprovalEnabled:
                    ResourcePolicyService.attach_resource_policy(
                        session=session,
                        group=share.groupUri,
                        permissions=SHARE_OBJECT_APPROVER,
                        resource_uri=share.shareUri,
                        resource_type=ShareObject.__name__,
                    )
                    share = cls.approve_share_object_extension(uri=share.shareUri)

                activity = Activity(
                    action='SHARE_OBJECT:EXTENSION_REQUEST',
                    label='SHARE_OBJECT:EXTENSION_REQUEST',
                    owner=get_context().username,
                    summary=f'{get_context().username} submitted share extension request for {dataset.name} in environment with URI: {dataset.environmentUri} for the principal: {share.principalRoleName}',
                    targetUri=dataset.datasetUri,
                    targetType='dataset',
                )

                session.add(activity)

                return share
            else:
                raise Exception("Share expiration cannot be extended as the dataset doesn't have expiration enabled")

    @classmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_SHARES)
    @ResourcePolicyService.has_resource_permission(APPROVE_SHARE_OBJECT)
    def approve_share_object(cls, uri: str):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            share, dataset, states = cls._get_share_data(session, uri)
            cls.validate_share_object(
                share_action=ShareObjectActions.Approve,
                dataset_type=dataset.datasetType,
                session=session,
                dataset=dataset,
                share=share,
            )

            if dataset.enableExpiration and share.requestedExpiryDate and share.requestedExpiryDate < datetime.today():
                raise Exception(
                    'Cannot approve share since its it past the requested expiration date. Please reject this share and submit a new share request'
                )

            cls._run_transitions(session, share, states, ShareObjectActions.Approve)

            share.rejectPurpose = ''
            # Use share.requestedExpiryDate when a share is newly created.
            # After first approval, if new items are added are approved, use the shareExpiryDate which is already set
            share.expiryDate = (
                share.requestedExpiryDate
                if (share.submittedForExtension or share.expiryDate is None)
                else share.expiryDate
            )
            share.requestedExpiryDate = None
            share.submittedForExtension = False

            ShareNotificationService(session=session, dataset=dataset, share=share).notify_share_object_approval(
                email_id=context.username
            )

            approve_share_task: Task = Task(
                action='ecs.share.approve',
                targetUri=uri,
                payload={'environmentUri': share.environmentUri},
            )
            session.add(approve_share_task)

        Worker.queue(engine=context.db_engine, task_ids=[approve_share_task.taskUri])
        return share

    @classmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_SHARES)
    @ResourcePolicyService.has_resource_permission(APPROVE_SHARE_OBJECT)
    def approve_share_object_extension(cls, uri: str):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            share, dataset, states = cls._get_share_data(session, uri)

            cls.validate_share_object(
                share_action=ShareObjectActions.Approve,
                dataset_type=dataset.datasetType,
                session=session,
                dataset=dataset,
                share=share,
            )

            if dataset.enableExpiration and share.requestedExpiryDate and share.requestedExpiryDate < datetime.today():
                raise Exception(
                    'Cannot approve share extension since its it past the requested expiration date. Please reject this share and submit a new share request'
                )

            cls._run_transitions(session, share, states, ShareObjectActions.ExtensionApprove)

            share.rejectPurpose = ''
            share.expiryDate = share.requestedExpiryDate
            share.nonExpirable = False if share.requestedExpiryDate else share.nonExpirable
            share.requestedExpiryDate = None
            share.submittedForExtension = False
            share.lastExtensionDate = datetime.today()

            activity = Activity(
                action='SHARE_OBJECT:APPROVE_EXTENSION',
                label='SHARE_OBJECT:APPROVE_EXTENSION',
                owner=get_context().username,
                summary=f'{get_context().username} approved share extension request for {dataset.name} in environment with URI: {dataset.environmentUri} for the principal: {share.principalRoleName}',
                targetUri=dataset.datasetUri,
                targetType='dataset',
            )

            session.add(activity)

            ShareNotificationService(
                session=session, dataset=dataset, share=share
            ).notify_share_object_extension_approval(email_id=context.username)

        return share

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_SHARES)
    @ResourcePolicyService.has_resource_permission(SUBMIT_SHARE_OBJECT)
    def update_share_request_purpose(uri: str, request_purpose) -> bool:
        with get_context().db_engine.scoped_session() as session:
            share = ShareObjectRepository.get_share_by_uri(session, uri)
            share.requestPurpose = request_purpose
            session.commit()
            return True

    @classmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_SHARES)
    @ResourcePolicyService.has_resource_permission(SUBMIT_SHARE_OBJECT)
    def update_share_expiration_period(cls, uri: str, expiration, nonExpirable) -> bool:
        with get_context().db_engine.scoped_session() as session:
            share, dataset, states = cls._get_share_data(session, uri)
            if share.status not in [
                ShareObjectStatus.Submitted.value,
                ShareObjectStatus.Submitted_For_Extension.value,
                ShareObjectStatus.Draft.value,
            ]:
                raise Exception(
                    f"Cannot update share object's expiration as it is not in {', '.join([ShareObjectStatus.Submitted.value, ShareObjectStatus.Submitted_For_Extension.value, ShareObjectStatus.Draft.value])}"
                )

            invalid_states = [
                ShareItemStatus.Share_Succeeded.value,
                ShareItemStatus.Revoke_In_Progress.value,
                ShareItemStatus.Share_In_Progress.value,
                ShareItemStatus.Share_Approved.value,
                ShareItemStatus.Revoke_Approved.value,
            ]
            share_item_invalid_state = [state for state in states if states in invalid_states]

            if share_item_invalid_state:
                raise Exception(
                    f"Cannot update share object's expiration as it share items are in incorrect state {', '.join(invalid_states)}"
                )

            if nonExpirable:
                share.nonExpirable = nonExpirable
                share.expiryDate = None
                share.requestedExpiryDate = None
                share.shareExpirationPeriod = None
                session.commit()
                return True
            else:
                share.nonExpirable = False

            if dataset.enableExpiration and (
                expiration < dataset.expiryMinDuration or expiration > dataset.expiryMaxDuration
            ):
                raise InvalidInput(
                    param_name='Share Expiration',
                    param_value=expiration,
                    constraint=f'between {dataset.expiryMinDuration} and {dataset.expiryMaxDuration}',
                )

            if dataset.enableExpiration:
                expiration_date = ExpirationUtils.calculate_expiry_date(expiration, dataset.expirySetting)
            else:
                raise Exception("Couldn't update share expiration as dataset doesn't have share expiration enabled")
            share.requestedExpiryDate = expiration_date
            share.shareExpirationPeriod = expiration
            activity = Activity(
                action='SHARE_OBJECT:UPDATE_EXTENSION_PERIOD',
                label='SHARE_OBJECT:UPDATE_EXTENSION_PERIOD',
                owner=get_context().username,
                summary=f'{get_context().username} updated share extension period request for {dataset.name} in environment with URI: {dataset.environmentUri} for the principal: {share.principalRoleName}',
                targetUri=dataset.datasetUri,
                targetType='dataset',
            )

            session.add(activity)
            return True

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_SHARES)
    @ResourcePolicyService.has_resource_permission(REJECT_SHARE_OBJECT)
    def update_share_reject_purpose(uri: str, reject_purpose) -> bool:
        with get_context().db_engine.scoped_session() as session:
            share = ShareObjectRepository.get_share_by_uri(session, uri)
            share.rejectPurpose = reject_purpose
            session.commit()
            return True

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_SHARES)
    @ResourcePolicyService.has_resource_permission(SUBMIT_SHARE_OBJECT)
    def update_share_extension_purpose(uri: str, extension_purpose) -> bool:
        with get_context().db_engine.scoped_session() as session:
            share = ShareObjectRepository.get_share_by_uri(session, uri)
            share.extensionReason = extension_purpose
            return True

    @classmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_SHARES)
    @ResourcePolicyService.has_resource_permission(REJECT_SHARE_OBJECT)
    def reject_share_object(cls, uri: str, reject_purpose: str):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            share, dataset, states = cls._get_share_data(session, uri)
            if share.submittedForExtension:
                cls._run_transitions(session, share, states, ShareObjectActions.ExtensionReject)
            else:
                cls._run_transitions(session, share, states, ShareObjectActions.Reject)

            if share.submittedForExtension:
                ShareNotificationService(
                    session=session, dataset=dataset, share=share
                ).notify_share_object_extension_rejection(email_id=context.username)
            else:
                ShareNotificationService(session=session, dataset=dataset, share=share).notify_share_object_rejection(
                    email_id=context.username
                )

            # Update Reject Purpose
            share.rejectPurpose = reject_purpose
            share.submittedForExtension = False
            share.requestedExpiryDate = None
            share.nonExpirable = True if share.nonExpirable and share.expiryDate is None else False

            activity = Activity(
                action='SHARE_OBJECT:REJECT',
                label='SHARE_OBJECT:REJECT',
                owner=get_context().username,
                summary=f'{get_context().username} rejected share {"extension" if share.submittedForExtension else ""} request for {dataset.name} in environment with URI: {dataset.environmentUri} for the principal: {share.principalRoleName}',
                targetUri=dataset.datasetUri,
                targetType='dataset',
            )

            session.add(activity)

            return share

    @classmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_SHARES)
    @ResourcePolicyService.has_resource_permission(SUBMIT_SHARE_OBJECT)
    def cancel_share_object_extension(cls, uri: str) -> bool:
        with get_context().db_engine.scoped_session() as session:
            share, dataset, states = cls._get_share_data(session, uri)

            cls._run_transitions(session, share, states, ShareObjectActions.CancelExtension)

            share.submittedForExtension = False
            share.requestedExpiryDate = None
            share.nonExpirable = True if share.nonExpirable and share.expiryDate is None else False
            share.shareExpirationPeriod = None

            activity = Activity(
                action='SHARE_OBJECT:CANCEL_EXTENSION',
                label='SHARE_OBJECT:CANCEL_EXTENSION',
                owner=get_context().username,
                summary=f'{get_context().username} cancelled share extension request for {dataset.name} in environment with URI: {dataset.environmentUri} for the principal: {share.principalRoleName}',
                targetUri=dataset.datasetUri,
                targetType='dataset',
            )

            session.add(activity)

            return True

    @classmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_SHARES)
    @ResourcePolicyService.has_resource_permission(DELETE_SHARE_OBJECT)
    def delete_share_object(cls, uri: str, force_delete: bool):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            share, dataset, states = cls._get_share_data(session, uri)
            shared_share_items_states = [x for x in ShareStatusRepository.get_share_item_shared_states() if x in states]
            if shared_share_items_states and not force_delete:
                raise ShareItemsFound(
                    action='Delete share object',
                    message='There are shared items in this request. '
                    'Revoke access to these items before deleting the request.',
                )

            # Force clean-up of share AWS resources
            if force_delete:
                log.info('Triggering force clean-up task to revoke all share items')
                cleanup_share_task: Task = Task(
                    action='ecs.share.cleanup',
                    targetUri=uri,
                    payload={'environmentUri': share.environmentUri},
                )
                session.add(cleanup_share_task)
                session.commit()
                Worker.queue(engine=context.db_engine, task_ids=[cleanup_share_task.taskUri])

            else:
                ShareObjectService.deleting_share_permissions(session=session, share=share, dataset=dataset)
                # Delete all share items and share
                ShareStatusRepository.delete_share_item_batch(session=session, share_uri=share.shareUri)
                session.delete(share)
            return True

    @staticmethod
    def deleting_share_permissions(session, share, dataset):
        # Delete share resource policy permissions
        # Deleting REQUESTER permissions
        ResourcePolicyService.delete_resource_policy(
            session=session,
            group=share.groupUri,
            resource_uri=share.shareUri,
        )

        # Deleting APPROVER permissions
        ResourcePolicyService.delete_resource_policy(
            session=session,
            group=dataset.SamlAdminGroupName,
            resource_uri=share.shareUri,
        )
        if dataset.stewards != dataset.SamlAdminGroupName:
            ResourcePolicyService.delete_resource_policy(
                session=session,
                group=dataset.stewards,
                resource_uri=share.shareUri,
            )
        return True

    @staticmethod
    def resolve_share_object_statistics(uri):
        with get_context().db_engine.scoped_session() as session:
            shared_items = ShareStatusRepository.count_items_in_states(
                session, uri, ShareStatusRepository.get_share_item_shared_states()
            )
            revoked_items = ShareStatusRepository.count_items_in_states(
                session, uri, [ShareItemStatus.Revoke_Succeeded.value]
            )
            failed_states = [ShareItemStatus.Share_Failed.value, ShareItemStatus.Revoke_Failed.value]
            failed_items = ShareStatusRepository.count_items_in_states(session, uri, failed_states)
            pending_items = ShareStatusRepository.count_items_in_states(
                session, uri, [ShareItemStatus.PendingApproval.value]
            )
            return {
                'sharedItems': shared_items,
                'revokedItems': revoked_items,
                'failedItems': failed_items,
                'pendingItems': pending_items,
            }

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
        dataset = DatasetBaseRepository.get_dataset_by_uri(session, share.datasetUri)
        share_items_states = ShareStatusRepository.get_share_items_states(session, uri)
        return share, dataset, share_items_states

    @staticmethod
    def _validate_group_membership(session, share_object_group, environment_uri):
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

    @staticmethod
    def _resolve_principal_role_name(
        session, group_uri, environment_uri, principal_id, principal_role_name, principal_type
    ):
        if principal_type == PrincipalType.ConsumptionRole.value:
            consumption_role: ConsumptionRole = EnvironmentService.get_environment_consumption_role(
                session, principal_id, environment_uri
            )
            return consumption_role.IAMRoleName
        elif principal_type == PrincipalType.Group.value:
            env_group: EnvironmentGroup = EnvironmentService.get_environment_group(session, group_uri, environment_uri)
            return env_group.environmentIAMRoleName
        else:
            return principal_role_name
