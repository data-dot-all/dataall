import logging

from dataall import db
from dataall import utils
from dataall.api.Objects.Principal.resolvers import get_principal
from dataall.api.context import Context
from dataall.db import models
from dataall.db.exceptions import RequiredParameter
from dataall.modules.dataset_sharing.api.enums import ShareObjectPermission
from dataall.modules.dataset_sharing.db.models import ShareObjectItem, ShareObject
from dataall.modules.dataset_sharing.services.share_item_service import ShareItemService
from dataall.modules.dataset_sharing.services.share_object_service import ShareObjectService
from dataall.modules.datasets_base.db.dataset_repository import DatasetRepository
from dataall.modules.datasets_base.db.models import DatasetStorageLocation, DatasetTable, Dataset

log = logging.getLogger(__name__)


def create_share_object(
    context: Context,
    source,
    datasetUri: str = None,
    itemUri: str = None,
    itemType: str = None,
    input: dict = None,
):
    if not input:
        raise RequiredParameter(input)
    if 'principalId' not in input:
        raise RequiredParameter('principalId')
    if 'principalType' not in input:
        raise RequiredParameter('principalType')
    if 'groupUri' not in input:
        raise RequiredParameter('groupUri')

    return ShareObjectService.create_share_object(
        uri=input['environmentUri'],
        dataset_uri=datasetUri,
        item_uri=itemUri,
        item_type=itemType,
        group_uri=input['groupUri'],
        principal_id=input['principalId'],
        principal_type=input['principalType']
    )


def submit_share_object(context: Context, source, shareUri: str = None):
    return ShareObjectService.submit_share_object(uri=shareUri)


def approve_share_object(context: Context, source, shareUri: str = None):
    return ShareObjectService.approve_share_object(uri=shareUri)


def reject_share_object(context: Context, source, shareUri: str = None):
    return ShareObjectService.reject_share_object(uri=shareUri)


def revoke_items_share_object(context: Context, source, input):
    share_uri = input.get("shareUri")
    revoked_uris = input.get("revokedItemUris")
    return ShareItemService.revoke_items_share_object(uri=share_uri, revoked_uris=revoked_uris)


def delete_share_object(context: Context, source, shareUri: str = None):
    return ShareObjectService.delete_share_object(uri=shareUri)


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


def resolve_user_role(context: Context, source: ShareObject, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        dataset: Dataset = DatasetRepository.get_dataset_by_uri(session, source.datasetUri)
        if dataset and dataset.stewards in context.groups:
            return ShareObjectPermission.Approvers.value
        if (
            source.owner == context.username
            or source.principalId in context.groups
            or dataset.owner == context.username
            or dataset.SamlAdminGroupName in context.groups
        ):
            return ShareObjectPermission.Requesters.value
        if (
            dataset and dataset.stewards in context.groups
            and (
                source.owner == context.username
                or source.principalId in context.groups
                or dataset.owner == context.username
                or dataset.SamlAdminGroupName in context.groups
            )
        ):
            return ShareObjectPermission.ApproversAndRequesters.value
        else:
            return ShareObjectPermission.NoPermission.value


def resolve_dataset(context: Context, source: ShareObject, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        ds: Dataset = DatasetRepository.get_dataset_by_uri(session, source.datasetUri)
        if ds:
            env: models.Environment = db.api.Environment.get_environment_by_uri(session, ds.environmentUri)
            return {
                'datasetUri': source.datasetUri,
                'datasetName': ds.name if ds else 'NotFound',
                'SamlAdminGroupName': ds.SamlAdminGroupName if ds else 'NotFound',
                'environmentName': env.label if env else 'NotFound',
                'AwsAccountId': env.AwsAccountId if env else 'NotFound',
                'region': env.region if env else 'NotFound',
                'exists': True if ds else False,
            }


def union_resolver(object, *_):
    if isinstance(object, DatasetTable):
        return 'DatasetTable'
    elif isinstance(object, DatasetStorageLocation):
        return 'DatasetStorageLocation'


def resolve_principal(context: Context, source: ShareObject, **kwargs):
    if not source:
        return None

    with context.engine.scoped_session() as session:
        return get_principal(
            session, source.principalId, source.principalType, source.principalIAMRoleName, source.environmentUri, source.groupUri
        )


def resolve_group(context: Context, source: ShareObject, **kwargs):
    if not source:
        return None
    return source.groupUri


def resolve_consumption_data(context: Context, source: ShareObject, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        ds: Dataset = DatasetRepository.get_dataset_by_uri(session, source.datasetUri)
        if ds:
            S3AccessPointName = utils.slugify(
                source.datasetUri + '-' + source.principalId,
                max_length=50, lowercase=True, regex_pattern='[^a-zA-Z0-9-]', separator='-'
            )
            return {
                's3AccessPointName': S3AccessPointName,
                'sharedGlueDatabase': (ds.GlueDatabaseName + '_shared_' + source.shareUri)[:254] if ds else 'Not created',
            }


def resolve_share_object_statistics(context: Context, source: ShareObject, **kwargs):
    if not source:
        return None
    return ShareObjectService.resolve_share_object_statistics(uri=source.shareUri)


def resolve_existing_shared_items(context: Context, source: ShareObject, **kwargs):
    if not source:
        return None
    return ShareItemService.check_existing_shared_items(source)


def list_shareable_objects(
    context: Context, source: ShareObject, filter: dict = None
):
    if not source:
        return None
    if not filter:
        filter = {'page': 1, 'pageSize': 5}

    is_revokable = filter.get('isRevokable')
    return ShareItemService.list_shareable_objects(
        share=source,
        is_revokable=is_revokable,
        filter=filter
    )


def list_shares_in_my_inbox(context: Context, source, filter: dict = None):
    if not filter:
        filter = {}
    return ShareObjectService.list_shares_in_my_inbox(filter)


def list_shares_in_my_outbox(context: Context, source, filter: dict = None):
    if not filter:
        filter = {}
    return ShareObjectService.list_shares_in_my_outbox(filter)


def list_shared_with_environment_data_items(
    context: Context, source, environmentUri: str = None, filter: dict = None
):
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        return ShareItemService.paginated_shared_with_environment_datasets(
            session=session,
            uri=environmentUri,
            data=filter,
        )
