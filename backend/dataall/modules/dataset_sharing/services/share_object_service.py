from datetime import datetime
from warnings import warn

from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.core.tasks.service_handlers import Worker
from dataall.base.context import get_context
from dataall.core.activity.db.activity_models import Activity
from dataall.core.environment.db.environment_models import EnvironmentGroup, ConsumptionRole
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.permissions.services.environment_permissions import GET_ENVIRONMENT
from dataall.core.tasks.db.task_models import Task
from dataall.base.db import utils
from dataall.base.aws.quicksight import QuicksightClient
from dataall.base.db.exceptions import UnauthorizedOperation
from dataall.modules.dataset_sharing.services.dataset_sharing_enums import (
    ShareObjectActions,
    ShareableType,
    ShareItemStatus,
    ShareObjectStatus,
    PrincipalType,
    ShareItemHealthStatus,
)
from dataall.modules.dataset_sharing.db.share_object_models import ShareObjectItem, ShareObject
from dataall.modules.dataset_sharing.db.share_object_repositories import (
    ShareObjectRepository,
    ShareObjectSM,
    ShareItemSM,
)
from dataall.modules.dataset_sharing.services.share_exceptions import ShareItemsFound, PrincipalRoleNotFound
from dataall.modules.dataset_sharing.services.share_item_service import ShareItemService
from dataall.modules.dataset_sharing.services.share_notification_service import ShareNotificationService
from dataall.modules.dataset_sharing.services.managed_share_policy_service import SharePolicyService
from dataall.modules.dataset_sharing.services.share_permissions import (
    REJECT_SHARE_OBJECT,
    APPROVE_SHARE_OBJECT,
    SUBMIT_SHARE_OBJECT,
    SHARE_OBJECT_APPROVER,
    SHARE_OBJECT_REQUESTER,
    CREATE_SHARE_OBJECT,
    DELETE_SHARE_OBJECT,
    GET_SHARE_OBJECT,
)
from dataall.modules.dataset_sharing.aws.glue_client import GlueClient
from dataall.modules.datasets.db.dataset_repositories import DatasetRepository
from dataall.modules.datasets.db.dataset_models import DatasetTable, Dataset, DatasetStorageLocation
from dataall.modules.datasets.services.dataset_permissions import DATASET_TABLE_READ, DATASET_FOLDER_READ
from dataall.base.aws.iam import IAM

import logging

log = logging.getLogger(__name__)


class ShareObjectService:
    @staticmethod
    def verify_principal_role(session, share: ShareObject) -> bool:
        role_name = share.principalIAMRoleName
        env = EnvironmentService.get_environment_by_uri(session, share.environmentUri)
        principal_role = IAM.get_role_arn_by_name(account_id=env.AwsAccountId, region=env.region, role_name=role_name)
        return principal_role is not None

    @staticmethod
    def update_all_share_items_status(
        session, shareUri, new_health_status: str, message, previous_health_status: str = None
    ):
        for item in ShareObjectRepository.get_all_shareable_items(
            session, shareUri, healthStatus=previous_health_status
        ):
            ShareObjectRepository.update_share_item_health_status(
                session,
                share_item=item,
                healthStatus=new_health_status,
                healthMessage=message,
                timestamp=datetime.now(),
            )

    @staticmethod
    @ResourcePolicyService.has_resource_permission(GET_ENVIRONMENT)
    def get_share_object_in_environment(uri, shareUri):
        with get_context().db_engine.scoped_session() as session:
            return ShareObjectRepository.get_share_by_uri(session, shareUri)

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
        principal_type,
        requestPurpose,
        attachMissingPolicies,
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
                    session, principal_id, environment.environmentUri
                )
                principal_iam_role_name = consumption_role.IAMRoleName
                managed = consumption_role.dataallManaged

            else:
                env_group: EnvironmentGroup = EnvironmentService.get_environment_group(
                    session, group_uri, environment.environmentUri
                )
                principal_iam_role_name = env_group.environmentIAMRoleName
                managed = True

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

            share_policy_service = SharePolicyService(
                account=environment.AwsAccountId,
                region=environment.region,
                role_name=principal_iam_role_name,
                environmentUri=environment.environmentUri,
                resource_prefix=environment.resourcePrefix,
            )
            # Backwards compatibility
            # we check if a managed share policy exists. If False, the role was introduced to data.all before this update
            # We create the policy from the inline statements
            # In this case it could also happen that the role is the Admin of the environment
            if not share_policy_service.check_if_policy_exists():
                share_policy_service.create_managed_policy_from_inline_and_delete_inline()
            # End of backwards compatibility

            attached = share_policy_service.check_if_policy_attached()
            if not attached and not managed and not attachMissingPolicies:
                raise Exception(
                    f'Required customer managed policy {share_policy_service.generate_policy_name()} is not attached to role {principal_iam_role_name}'
                )
            elif not attached:
                share_policy_service.attach_policy()
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
                    requestPurpose=requestPurpose,
                )
                ShareObjectRepository.save_and_commit(session, share)

            if item_uri:
                item = ShareObjectRepository.get_share_item(session, item_type, item_uri)
                share_item = ShareObjectRepository.find_sharable_item(session, share.shareUri, item_uri)

                s3_access_point_name = utils.slugify(
                    share.datasetUri + '-' + share.principalId,
                    max_length=50,
                    lowercase=True,
                    regex_pattern='[^a-zA-Z0-9-]',
                    separator='-',
                )

                if not share_item and item:
                    new_share_item: ShareObjectItem = ShareObjectItem(
                        shareUri=share.shareUri,
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
            return share

    @classmethod
    @ResourcePolicyService.has_resource_permission(SUBMIT_SHARE_OBJECT)
    def submit_share_object(cls, uri: str):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            share, dataset, states = cls._get_share_data(session, uri)

            if not ShareObjectService.verify_principal_role(session, share):
                raise PrincipalRoleNotFound(
                    action='Submit Share Object',
                    message=f'The principal role {share.principalIAMRoleName} is not found.',
                )

            valid_states = [ShareItemStatus.PendingApproval.value]
            valid_share_items_states = [x for x in valid_states if x in states]

            if not valid_share_items_states:
                raise ShareItemsFound(
                    action='Submit Share Object',
                    message='The request is empty of pending items. Add items to share request.',
                )

            env = EnvironmentService.get_environment_by_uri(session, share.environmentUri)
            dashboard_enabled = EnvironmentService.get_boolean_env_param(session, env, 'dashboardsEnabled')
            if dashboard_enabled:
                share_table_items = ShareObjectRepository.find_all_share_items(session, uri, ShareableType.Table.value)
                if share_table_items:
                    QuicksightClient.check_quicksight_enterprise_subscription(
                        AwsAccountId=env.AwsAccountId, region=env.region
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

            if not ShareObjectService.verify_principal_role(session, share):
                raise PrincipalRoleNotFound(
                    action='Approve Share Object',
                    message=f'The principal role {share.principalIAMRoleName} is not found.',
                )

            cls._run_transitions(session, share, states, ShareObjectActions.Approve)

            if share.groupUri != dataset.SamlAdminGroupName and share.principalType == PrincipalType.Group.value:
                log.info('Attaching TABLE/FOLDER READ permissions...')
                ShareObjectService._attach_dataset_table_read_permission(session, share)
                ShareObjectService._attach_dataset_folder_read_permission(session, share)

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
            shared_share_items_states = [x for x in ShareItemSM.get_share_item_shared_states() if x in states]

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
            tables = ShareObjectRepository.count_sharable_items(session, uri, 'DatasetTable')
            locations = ShareObjectRepository.count_sharable_items(session, uri, 'DatasetStorageLocation')
            shared_items = ShareObjectRepository.count_items_in_states(
                session, uri, ShareItemSM.get_share_item_shared_states()
            )
            revoked_items = ShareObjectRepository.count_items_in_states(
                session, uri, [ShareItemStatus.Revoke_Succeeded.value]
            )
            failed_states = [ShareItemStatus.Share_Failed.value, ShareItemStatus.Revoke_Failed.value]
            failed_items = ShareObjectRepository.count_items_in_states(session, uri, failed_states)
            pending_items = ShareObjectRepository.count_items_in_states(
                session, uri, [ShareItemStatus.PendingApproval.value]
            )
            return {
                'tables': tables,
                'locations': locations,
                'sharedItems': shared_items,
                'revokedItems': revoked_items,
                'failedItems': failed_items,
                'pendingItems': pending_items,
            }

    @staticmethod
    def resolve_share_object_consumption_data(uri, datasetUri, principalId, environmentUri):
        with get_context().db_engine.scoped_session() as session:
            dataset = DatasetRepository.get_dataset_by_uri(session, datasetUri)
            if dataset:
                environment = EnvironmentService.get_environment_by_uri(session, environmentUri)
                S3AccessPointName = utils.slugify(
                    datasetUri + '-' + principalId,
                    max_length=50,
                    lowercase=True,
                    regex_pattern='[^a-zA-Z0-9-]',
                    separator='-',
                )
                # Check if the share was made with a Glue Database
                datasetGlueDatabase = ShareItemService._get_glue_database_for_share(
                    dataset.GlueDatabaseName, dataset.AwsAccountId, dataset.region
                )
                old_shared_db_name = f'{datasetGlueDatabase}_shared_{uri}'[:254]
                database = GlueClient(
                    account_id=environment.AwsAccountId, region=environment.region, database=old_shared_db_name
                ).get_glue_database()
                warn('old_shared_db_name will be deprecated in v2.6.0', DeprecationWarning, stacklevel=2)
                sharedGlueDatabase = old_shared_db_name if database else f'{datasetGlueDatabase}_shared'
                return {
                    's3AccessPointName': S3AccessPointName,
                    'sharedGlueDatabase': sharedGlueDatabase,
                    's3bucketName': dataset.S3BucketName,
                }
            return {
                's3AccessPointName': 'Not Created',
                'sharedGlueDatabase': 'Not Created',
                's3bucketName': 'Not Created',
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
        dataset = DatasetRepository.get_dataset_by_uri(session, share.datasetUri)
        share_items_states = ShareObjectRepository.get_share_items_states(session, uri)
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
    def _attach_dataset_table_read_permission(session, share):
        """
        Attach Table permissions to share groups
        """
        share_table_items = ShareObjectRepository.find_all_share_items(
            session, share.shareUri, ShareableType.Table.value, [ShareItemStatus.Share_Approved.value]
        )
        for table in share_table_items:
            ResourcePolicyService.attach_resource_policy(
                session=session,
                group=share.groupUri,
                permissions=DATASET_TABLE_READ,
                resource_uri=table.itemUri,
                resource_type=DatasetTable.__name__,
            )

    @staticmethod
    def _attach_dataset_folder_read_permission(session, share):
        """
        Attach Table permissions to share groups
        """
        share_folder_items = ShareObjectRepository.find_all_share_items(
            session, share.shareUri, ShareableType.StorageLocation.value, [ShareItemStatus.Share_Approved.value]
        )
        for location in share_folder_items:
            ResourcePolicyService.attach_resource_policy(
                session=session,
                group=share.groupUri,
                permissions=DATASET_FOLDER_READ,
                resource_uri=location.itemUri,
                resource_type=DatasetStorageLocation.__name__,
            )
