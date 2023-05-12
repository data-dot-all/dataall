import logging

from dataall import db
from dataall import utils
from dataall.api.Objects.Principal.resolvers import get_principal
from dataall.api.context import Context
from dataall.aws.handlers.service_handlers import Worker
from dataall.db import models
from dataall.modules.dataset_sharing.api.enums import ShareObjectPermission
from dataall.modules.dataset_sharing.db.models import ShareObjectItem, ShareObject
from dataall.modules.dataset_sharing.services.dataset_share_service import DatasetShareService
from dataall.modules.dataset_sharing.db.share_object_repository import ShareObjectRepository
from dataall.modules.datasets_base.db.dataset_repository import DatasetRepository
from dataall.modules.datasets_base.db.models import DatasetStorageLocation, DatasetTable, Dataset

log = logging.getLogger(__name__)


def get_share_object_dataset(context, source, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        share: ShareObject = session.query(ShareObject).get(
            source.shareUri
        )
        return session.query(Dataset).get(share.datasetUri)


def create_share_object(
    context: Context,
    source,
    datasetUri: str = None,
    itemUri: str = None,
    itemType: str = None,
    input: dict = None,
):

    with context.engine.scoped_session() as session:
        dataset: Dataset = DatasetRepository.get_dataset_by_uri(session, datasetUri)
        environment: models.Environment = db.api.Environment.get_environment_by_uri(
            session, input['environmentUri']
        )
        input['dataset'] = dataset
        input['environment'] = environment
        input['itemUri'] = itemUri
        input['itemType'] = itemType
        input['datasetUri'] = datasetUri
        return ShareObjectRepository.create_share_object(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=environment.environmentUri,
            data=input,
        )


def submit_share_object(context: Context, source, shareUri: str = None):
    with context.engine.scoped_session() as session:
        return ShareObjectRepository.submit_share_object(
            session=session,
            username=context.username,
            uri=shareUri,
        )


def approve_share_object(context: Context, source, shareUri: str = None):
    with context.engine.scoped_session() as session:
        share = ShareObjectRepository.approve_share_object(
            session=session,
            username=context.username,
            uri=shareUri,
        )

        approve_share_task: models.Task = models.Task(
            action='ecs.share.approve',
            targetUri=shareUri,
            payload={'environmentUri': share.environmentUri},
        )
        session.add(approve_share_task)

    Worker.queue(engine=context.engine, task_ids=[approve_share_task.taskUri])

    return share


def reject_share_object(context: Context, source, shareUri: str = None):
    with context.engine.scoped_session() as session:
        return ShareObjectRepository.reject_share_object(
            session=session,
            username=context.username,
            uri=shareUri,
        )


def revoke_items_share_object(context: Context, source, input):
    with context.engine.scoped_session() as session:
        share = ShareObjectRepository.revoke_items_share_object(
            session=session,
            username=context.username,
            uri=input.get("shareUri"),
            data=input,
        )

        revoke_share_task: models.Task = models.Task(
            action='ecs.share.revoke',
            targetUri=input.get("shareUri"),
            payload={'environmentUri': share.environmentUri},
        )
        session.add(revoke_share_task)

    Worker.queue(engine=context.engine, task_ids=[revoke_share_task.taskUri])

    return share


def delete_share_object(context: Context, source, shareUri: str = None):
    with context.engine.scoped_session() as session:
        share = ShareObjectRepository.get_share_by_uri(session, shareUri)
        if not share:
            raise db.exceptions.ObjectNotFound('ShareObject', shareUri)

        ShareObjectRepository.delete_share_object(session=session, uri=shareUri)

    return True


def add_shared_item(context, source, shareUri: str = None, input: dict = None):
    with context.engine.scoped_session() as session:
        share_item = ShareObjectRepository.add_share_object_item(
            session=session,
            username=context.username,
            uri=shareUri,
            data=input,
        )
    return share_item


def remove_shared_item(context, source, shareItemUri: str = None):
    with context.engine.scoped_session() as session:
        share_item: ShareObjectItem = session.query(ShareObjectItem).get(
            shareItemUri
        )
        if not share_item:
            raise db.exceptions.ObjectNotFound('ShareObjectItem', shareItemUri)
        share = ShareObjectRepository.get_share_by_uri(session, share_item.shareUri)
        ShareObjectRepository.remove_share_object_item(
            session=session,
            uri=share.shareUri,
            data={
                'shareItemUri': shareItemUri,
                'share_item': share_item,
                'share': share,
            }
        )
    return True


def list_shared_items(
    context: Context, source: ShareObject, filter: dict = None
):
    if not source:
        return None
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        return ShareObjectRepository.list_shared_items(
            session=session,
            username=context.username,
            data=filter,
        )


def resolve_shared_item(context, source: ShareObjectItem, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        return ShareObjectRepository.get_share_item(
            session=session,
            uri=source.shareUri,
            data={'share_item': source},
        )


def get_share_object(context, source, shareUri: str = None):
    with context.engine.scoped_session() as session:
        return ShareObjectRepository.get_share_object(
            session=session,
            uri=shareUri,
        )


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
    with context.engine.scoped_session() as session:
        return ShareObjectRepository.resolve_share_object_statistics(
            session, source.shareUri
        )


def resolve_existing_shared_items(context: Context, source: ShareObject, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        return ShareObjectRepository.check_existing_shared_items(
            session, source.shareUri
        )


def list_shareable_objects(
    context: Context, source: ShareObject, filter: dict = None
):
    if not source:
        return None
    if not filter:
        filter = {'page': 1, 'pageSize': 5}
    with context.engine.scoped_session() as session:
        return ShareObjectRepository.list_shareable_items(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=source.shareUri,
            data=filter,
            check_perm=True,
        )


def list_shares_in_my_inbox(context: Context, source, filter: dict = None):
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        return ShareObjectRepository.list_user_received_share_requests(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=None,
            data=filter,
            check_perm=None,
        )


def list_shares_in_my_outbox(context: Context, source, filter: dict = None):
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        return ShareObjectRepository.list_user_sent_share_requests(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=None,
            data=filter,
            check_perm=None,
        )


def list_data_items_shared_with_env_group(
    context, source, environmentUri: str = None, groupUri: str = None, filter: dict = None
):
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        return DatasetShareService.paginated_shared_with_environment_group_datasets(
            session=session,
            username=context.username,
            groups=context.groups,
            envUri=environmentUri,
            groupUri=groupUri,
            data=filter,
            check_perm=True,
        )


def list_shared_with_environment_data_items(
    context: Context, source, environmentUri: str = None, filter: dict = None
):
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        return DatasetShareService.paginated_shared_with_environment_datasets(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=environmentUri,
            data=filter,
            check_perm=True,
        )
