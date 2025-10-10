import logging
import re

from dataall.base.api.context import Context
from dataall.base.db.exceptions import RequiredParameter
from dataall.core.environment.db.environment_models import Environment
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.modules.datasets_base.db.dataset_models import DatasetBase
from dataall.modules.datasets_base.db.dataset_repositories import DatasetBaseRepository
from dataall.modules.shares_base.services.shares_enums import ShareObjectPermission, PrincipalType
from dataall.modules.shares_base.db.share_object_models import ShareObjectItem, ShareObject
from dataall.modules.shares_base.services.share_item_service import ShareItemService
from dataall.modules.shares_base.services.share_object_service import ShareObjectService
from dataall.modules.shares_base.services.share_logs_service import ShareLogsService
from dataall.base.utils.naming_convention import (
    NamingConventionService,
    NamingConventionPattern,
)

log = logging.getLogger(__name__)


class RequestValidator:
    @staticmethod
    def validate_creation_request(data):
        if not data:
            raise RequiredParameter(data)
        if not data.get('principalId'):
            raise RequiredParameter('principalId')
        if not data.get('principalType'):
            raise RequiredParameter('principalType')
        if not data.get('groupUri'):
            raise RequiredParameter('groupUri')
        if len(data.get('permissions', [])) == 0:
            raise RequiredParameter('permissions')

    @staticmethod
    def validate_item_selector_input(data):
        if not data:
            raise RequiredParameter(data)
        if not data.get('shareUri'):
            raise RequiredParameter('shareUri')
        if not data.get('itemUris'):
            raise RequiredParameter('itemUris')

    @staticmethod
    def validate_dataset_share_selector_input(data):
        if not data:
            raise RequiredParameter(data)
        if not data.get('datasetUri'):
            raise RequiredParameter('datasetUri')
        if not data.get('shareUris'):
            raise RequiredParameter('shareUris')

    @staticmethod
    def validate_update_share_item_filters(data):
        if not data.get('shareItemUri'):
            RequiredParameter('shareItemUri')
        if not data:
            raise RequiredParameter(data)
        if not data.get('filterUris'):
            raise RequiredParameter('filterUris')
        if not data.get('filterNames'):
            raise RequiredParameter('filterNames')
        NamingConventionService(
            target_label=data.get('label'),
            pattern=NamingConventionPattern.DATA_FILTERS,
        ).validate_name()


def create_share_object(
    context: Context,
    source,
    datasetUri: str = None,
    itemUri: str = None,
    itemType: str = None,
    input: dict = None,
):
    RequestValidator.validate_creation_request(input)

    return ShareObjectService.create_share_object(
        uri=input['environmentUri'],
        dataset_uri=datasetUri,
        item_uri=itemUri,
        item_type=itemType,
        group_uri=input['groupUri'],
        principal_id=input['principalId'],
        principal_role_name=input.get('principalRoleName'),
        principal_type=input['principalType'],
        requestPurpose=input.get('requestPurpose'),
        attachMissingPolicies=input.get('attachMissingPolicies', False),
        permissions=input.get('permissions'),
        shareExpirationPeriod=input.get('shareExpirationPeriod'),
        nonExpirable=input.get('nonExpirable', False),
    )


def submit_share_object(context: Context, source, shareUri: str = None):
    return ShareObjectService.submit_share_object(uri=shareUri)


def submit_share_extension(
    context: Context,
    source,
    shareUri: str = None,
    expiration: int = 0,
    extensionReason: str = None,
    nonExpirable: bool = False,
):
    return ShareObjectService.submit_share_extension(
        uri=shareUri, expiration=expiration, extension_reason=extensionReason, nonExpirable=nonExpirable
    )


def approve_share_object(context: Context, source, shareUri: str = None):
    return ShareObjectService.approve_share_object(uri=shareUri)


def approve_share_object_extension(context: Context, source, shareUri: str = None):
    return ShareObjectService.approve_share_object_extension(uri=shareUri)


def reject_share_object(
    context: Context,
    source,
    shareUri: str = None,
    rejectPurpose: str = None,
):
    return ShareObjectService.reject_share_object(uri=shareUri, reject_purpose=rejectPurpose)


def revoke_items_share_object(context: Context, source, input):
    RequestValidator.validate_item_selector_input(input)
    share_uri = input.get('shareUri')
    revoked_uris = input.get('itemUris')
    return ShareItemService.revoke_items_share_object(uri=share_uri, revoked_uris=revoked_uris)


def verify_items_share_object(context: Context, source, input):
    RequestValidator.validate_item_selector_input(input)
    share_uri = input.get('shareUri')
    verify_item_uris = input.get('itemUris')
    return ShareItemService.verify_items_share_object(uri=share_uri, item_uris=verify_item_uris)


def reapply_items_share_object(context: Context, source, input):
    RequestValidator.validate_item_selector_input(input)
    share_uri = input.get('shareUri')
    reapply_item_uris = input.get('itemUris')
    return ShareItemService.reapply_items_share_object(uri=share_uri, item_uris=reapply_item_uris)


def delete_share_object(context: Context, source, shareUri: str = None, forceDelete: bool = False):
    return ShareObjectService.delete_share_object(uri=shareUri, force_delete=forceDelete)


def cancel_share_object_extension(context: Context, source, shareUri: str = None):
    return ShareObjectService.cancel_share_object_extension(uri=shareUri)


def add_shared_item(context, source, shareUri: str = None, input: dict = None):
    return ShareItemService.add_shared_item(uri=shareUri, data=input)


def remove_shared_item(context, source, shareItemUri: str = None):
    return ShareItemService.remove_shared_item(uri=shareItemUri)


def resolve_shared_item(context, source: ShareObjectItem, **kwargs):
    if not source:
        return None
    return ShareItemService.resolve_shared_item(uri=source.shareUri, item=source)


def get_share_object(context, source, shareUri: str = None):
    return ShareObjectService.get_share_object(uri=shareUri)


def get_share_logs(context, source, shareUri: str):
    return ShareLogsService.get_share_logs(shareUri)


def resolve_user_role(context: Context, source: ShareObject, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        dataset: DatasetBase = DatasetBaseRepository.get_dataset_by_uri(session, source.datasetUri)

        can_approve = (
            True
            if (
                dataset
                and (
                    dataset.stewards in context.groups
                    or dataset.SamlAdminGroupName in context.groups
                    or dataset.owner == context.username
                )
            )
            else False
        )

        can_request = True if (source.owner == context.username or source.groupUri in context.groups) else False

        return (
            ShareObjectPermission.ApproversAndRequesters.value
            if can_approve and can_request
            else ShareObjectPermission.Approvers.value
            if can_approve
            else ShareObjectPermission.Requesters.value
            if can_request
            else ShareObjectPermission.NoPermission.value
        )


def resolve_can_view_logs(context: Context, source: ShareObject):
    try:
        return ShareLogsService.check_view_logs_permissions(source.shareUri)
    except Exception as e:
        log.error(f'Failed to check if user is allowed to view share logs due to: {e}')
        return False


def resolve_dataset(context: Context, source: ShareObject, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        ds: DatasetBase = DatasetBaseRepository.get_dataset_by_uri(session, source.datasetUri)
        if ds:
            env: Environment = EnvironmentService.get_environment_by_uri(session, ds.environmentUri)
            return {
                'datasetUri': source.datasetUri,
                'datasetName': ds.name if ds else 'NotFound',
                'SamlAdminGroupName': ds.SamlAdminGroupName if ds else 'NotFound',
                'environmentName': env.label if env else 'NotFound',
                'AwsAccountId': env.AwsAccountId if env else 'NotFound',
                'region': env.region if env else 'NotFound',
                'exists': True if ds else False,
                'description': ds.description,
                'datasetType': ds.datasetType,
                'enableExpiration': ds.enableExpiration,
                'expirySetting': ds.expirySetting,
            }


def resolve_principal(context: Context, source: ShareObject, **kwargs):
    if not source:
        return None

    with context.engine.scoped_session() as session:
        if source.principalType in set(item.value for item in PrincipalType):
            environment = EnvironmentService.get_environment_by_uri(session, source.environmentUri)
            if source.principalType == PrincipalType.ConsumptionRole.value:
                principal = EnvironmentService.get_environment_consumption_role(
                    session, source.principalId, source.environmentUri
                )
                principalName = f'{principal.consumptionRoleName} [{principal.IAMRoleArn}]'
            elif source.principalType == PrincipalType.Group.value:
                principal = EnvironmentService.get_environment_group(session, source.groupUri, source.environmentUri)
                principalName = f'{source.groupUri} [{principal.environmentIAMRoleArn}]'
            else:
                principalName = f'Redshift Role [{source.principalRoleName}]'

            return {
                'principalName': principalName,
                'principalId': source.principalId,
                'principalType': source.principalType,
                'principalRoleName': source.principalRoleName,
                'SamlGroupName': source.groupUri,
                'environmentName': environment.label,
            }


def resolve_group(context: Context, source: ShareObject, **kwargs):
    if not source:
        return None
    return source.groupUri


def resolve_share_object_statistics(context: Context, source: ShareObject, **kwargs):
    if not source:
        return None
    return ShareObjectService.resolve_share_object_statistics(uri=source.shareUri)


def resolve_existing_shared_items(context: Context, source: ShareObject, **kwargs):
    if not source:
        return None
    return ShareItemService.check_existing_shared_items(source)


def list_shareable_objects(context: Context, source: ShareObject, filter: dict = None):
    if not source:
        return None
    if not filter:
        filter = {'page': 1, 'pageSize': 5}

    is_revokable = filter.get('isRevokable')
    return ShareItemService.list_shareable_objects(share=source, is_revokable=is_revokable, filter=filter)


def list_shares_in_my_inbox(context: Context, source, filter: dict = None):
    if not filter:
        filter = {}
    return ShareObjectService.list_shares_in_my_inbox(filter)


def list_shares_in_my_outbox(context: Context, source, filter: dict = None):
    if not filter:
        filter = {}
    return ShareObjectService.list_shares_in_my_outbox(filter)


def list_shared_with_environment_data_items(context: Context, source, environmentUri: str = None, filter: dict = None):
    if not filter:
        filter = {}
    return ShareItemService.paginated_shared_with_environment_datasets(
        uri=environmentUri,
        data=filter,
    )


def update_share_request_purpose(context: Context, source, shareUri: str = None, requestPurpose: str = None):
    return ShareObjectService.update_share_request_purpose(
        uri=shareUri,
        request_purpose=requestPurpose,
    )


def update_share_reject_purpose(context: Context, source, shareUri: str = None, rejectPurpose: str = None):
    return ShareObjectService.update_share_reject_purpose(
        uri=shareUri,
        reject_purpose=rejectPurpose,
    )


def update_share_extension_purpose(context: Context, source, shareUri: str = None, extensionPurpose: str = None):
    return ShareObjectService.update_share_extension_purpose(
        uri=shareUri,
        extension_purpose=extensionPurpose,
    )


def update_filters_table_share_item(context: Context, source, input):
    RequestValidator.validate_update_share_item_filters(input)
    return ShareItemService.update_filters_table_share_item(uri=input.get('shareItemUri'), data=input)


def remove_filters_table_share_item(context: Context, source, attachedDataFilterUri: str = None):
    if not attachedDataFilterUri:
        RequiredParameter('attachedDataFilterUri')
    return ShareItemService.remove_share_item_data_filters(uri=attachedDataFilterUri)


def get_share_item_data_filters(context: Context, source, attachedDataFilterUri: str = None):
    if not attachedDataFilterUri:
        RequiredParameter('attachedDataFilterUri')
    return ShareItemService.get_share_item_data_filters(uri=attachedDataFilterUri)


def update_share_expiration_period(
    context: Context, source, shareUri: str = None, expiration: int = 0, nonExpirable: bool = False
):
    return ShareObjectService.update_share_expiration_period(
        uri=shareUri, expiration=expiration, nonExpirable=nonExpirable
    )
