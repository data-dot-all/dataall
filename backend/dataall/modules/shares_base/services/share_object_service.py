import os

from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.core.tasks.service_handlers import Worker
from dataall.base.context import get_context
from dataall.core.activity.db.activity_models import Activity
from dataall.core.environment.db.environment_models import EnvironmentGroup, ConsumptionRole
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.environment.services.managed_iam_policies import PolicyManager
from dataall.core.tasks.db.task_models import Task
from dataall.base.db.exceptions import UnauthorizedOperation
from dataall.modules.shares_base.services.shares_enums import (
    ShareObjectActions,
    ShareableType,
    ShareItemStatus,
    ShareObjectStatus,
    PrincipalType,
)
from dataall.modules.shares_base.db.share_object_models import ShareObjectItem, ShareObject
from dataall.modules.shares_base.db.share_object_repositories import ShareObjectRepository
from dataall.modules.shares_base.db.share_state_machines_repositories import ShareStatusRepository
from dataall.modules.shares_base.db.share_object_state_machines import (
    ShareObjectSM,
    ShareItemSM,
)
from dataall.modules.shares_base.services.share_exceptions import ShareItemsFound, PrincipalRoleNotFound
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
)
from dataall.modules.shares_base.services.share_processor_manager import ShareProcessorManager
from dataall.modules.datasets_base.db.dataset_repositories import DatasetBaseRepository
from dataall.modules.datasets_base.db.dataset_models import DatasetBase
from dataall.base.aws.iam import IAM

import logging

log = logging.getLogger(__name__)


class ShareObjectService:
    @staticmethod
    def verify_principal_role(session, share: ShareObject) -> bool:
        log.info('Verifying principal IAM role...')
        role_name = share.principalRoleName
        env = EnvironmentService.get_environment_by_uri(session, share.environmentUri)
        principal_role = IAM.get_role_arn_by_name(account_id=env.AwsAccountId, region=env.region, role_name=role_name)
        return principal_role is not None

    @staticmethod
    @ResourcePolicyService.has_resource_permission(GET_SHARE_OBJECT)
    def get_share_object(uri):
        with get_context().db_engine.scoped_session() as session:
            return ShareObjectRepository.get_share_by_uri(session, uri)

    @classmethod
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
    ):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            dataset: DatasetBase = DatasetBaseRepository.get_dataset_by_uri(session, dataset_uri)
            environment = EnvironmentService.get_environment_by_uri(session, uri)

            if environment.region != dataset.region:
                raise UnauthorizedOperation(
                    action=CREATE_SHARE_OBJECT,
                    message=f'Requester Team {group_uri} works in region {environment.region} '
                    f'and the requested dataset is stored in region {dataset.region}',
                )
            if (
                (dataset.stewards == group_uri or dataset.SamlAdminGroupName == group_uri)
                and environment.environmentUri == dataset.environmentUri
                and principal_type == PrincipalType.Group.value
            ):
                raise UnauthorizedOperation(
                    action=CREATE_SHARE_OBJECT,
                    message=f'Team: {group_uri} is managing the dataset {dataset.name}',
                )

            cls._validate_group_membership(session, group_uri, environment.environmentUri)

            if principal_type in [PrincipalType.ConsumptionRole.value, PrincipalType.Group.value]:
                if principal_type == PrincipalType.ConsumptionRole.value:
                    consumption_role: ConsumptionRole = EnvironmentService.get_environment_consumption_role(
                        session, principal_id, environment.environmentUri
                    )
                    principal_role_name = consumption_role.IAMRoleName
                    managed = consumption_role.dataallManaged

                else:
                    env_group: EnvironmentGroup = EnvironmentService.get_environment_group(
                        session, group_uri, environment.environmentUri
                    )
                    principal_role_name = env_group.environmentIAMRoleName
                    managed = True

                share_policy_manager = PolicyManager(
                    role_name=principal_role_name,
                    environmentUri=environment.environmentUri,
                    account=environment.AwsAccountId,
                    region=environment.region,
                    resource_prefix=environment.resourcePrefix,
                )
                for Policy in [
                    Policy for Policy in share_policy_manager.initializedPolicies if Policy.policy_type == 'SharePolicy'
                ]:
                    # Backwards compatibility
                    # we check if a managed share policy exists. If False, the role was introduced to data.all before this update
                    # We create the policy from the inline statements
                    # In this case it could also happen that the role is the Admin of the environment
                    if not Policy.check_if_policy_exists():
                        Policy.create_managed_policy_from_inline_and_delete_inline()
                    # End of backwards compatibility

                    attached = Policy.check_if_policy_attached()
                    if not attached and not managed and not attachMissingPolicies:
                        raise Exception(
                            f'Required customer managed policy {Policy.generate_policy_name()} is not attached to role {principal_role_name}'
                        )
                    elif not attached:
                        Policy.attach_policy()

            share = ShareObjectRepository.find_share(
                session=session,
                dataset=dataset,
                env=environment,
                principal_id=principal_id,
                principal_role_name=principal_role_name,
                group_uri=group_uri,
            )
            already_existed = share is not None
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
    @ResourcePolicyService.has_resource_permission(SUBMIT_SHARE_OBJECT)
    def submit_share_object(cls, uri: str):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            share, dataset, states = cls._get_share_data(session, uri)

            if share.principalType in [PrincipalType.ConsumptionRole.value, PrincipalType.Group.value]:
                # TODO make it generic to non IAM role principals
                if not ShareObjectService.verify_principal_role(session, share):
                    raise PrincipalRoleNotFound(
                        action='Submit Share Object',
                        message=f'The principal role {share.principalRoleName} is not found.',
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
    @ResourcePolicyService.has_resource_permission(APPROVE_SHARE_OBJECT)
    def approve_share_object(cls, uri: str):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            share, dataset, states = cls._get_share_data(session, uri)
            if share.principalType in [PrincipalType.ConsumptionRole.value, PrincipalType.Group.value]:
                if not ShareObjectService.verify_principal_role(
                    session, share
                ):  # TODO make it generic to non IAM role principals
                    raise PrincipalRoleNotFound(
                        action='Approve Share Object',
                        message=f'The principal role {share.principalRoleName} is not found.',
                    )

            cls._run_transitions(session, share, states, ShareObjectActions.Approve)

            share.rejectPurpose = ''
            session.commit()

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

    @staticmethod
    @ResourcePolicyService.has_resource_permission(SUBMIT_SHARE_OBJECT)
    def update_share_request_purpose(uri: str, request_purpose) -> bool:
        with get_context().db_engine.scoped_session() as session:
            share = ShareObjectRepository.get_share_by_uri(session, uri)
            share.requestPurpose = request_purpose
            session.commit()
            return True

    @staticmethod
    @ResourcePolicyService.has_resource_permission(REJECT_SHARE_OBJECT)
    def update_share_reject_purpose(uri: str, reject_purpose) -> bool:
        with get_context().db_engine.scoped_session() as session:
            share = ShareObjectRepository.get_share_by_uri(session, uri)
            share.rejectPurpose = reject_purpose
            session.commit()
            return True

    @classmethod
    @ResourcePolicyService.has_resource_permission(REJECT_SHARE_OBJECT)
    def reject_share_object(cls, uri: str, reject_purpose: str):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            share, dataset, states = cls._get_share_data(session, uri)
            cls._run_transitions(session, share, states, ShareObjectActions.Reject)

            # Update Reject Purpose
            share.rejectPurpose = reject_purpose
            session.commit()

            ShareNotificationService(session=session, dataset=dataset, share=share).notify_share_object_rejection(
                email_id=context.username
            )

            return share

    @classmethod
    @ResourcePolicyService.has_resource_permission(DELETE_SHARE_OBJECT)
    def delete_share_object(cls, uri: str):
        with get_context().db_engine.scoped_session() as session:
            share, dataset, states = cls._get_share_data(session, uri)
            shared_share_items_states = [x for x in ShareStatusRepository.get_share_item_shared_states() if x in states]

            new_state = cls._run_transitions(session, share, states, ShareObjectActions.Delete)
            if shared_share_items_states:
                raise ShareItemsFound(
                    action='Delete share object',
                    message='There are shared items in this request. '
                    'Revoke access to these items before deleting the request.',
                )

            if new_state == ShareObjectStatus.Deleted.value:
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

                # Delete share
                session.delete(share)

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
