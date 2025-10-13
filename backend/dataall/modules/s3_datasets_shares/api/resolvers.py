import logging

from dataall.base.api.context import Context
from dataall.base.db.exceptions import RequiredParameter
from dataall.base.feature_toggle_checker import is_feature_enabled
from dataall.modules.s3_datasets_shares.services.s3_share_service import S3ShareService

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


def list_shared_tables_by_env_dataset(context: Context, source, datasetUri: str, envUri: str):
    return S3ShareService.list_shared_tables_by_env_dataset(uri=envUri, dataset_uri=datasetUri)


@is_feature_enabled('modules.s3_datasets.features.aws_actions')
def get_dataset_shared_assume_role_url(context: Context, source, datasetUri: str = None):
    return S3ShareService.get_dataset_shared_assume_role_url(uri=datasetUri)


def verify_dataset_share_objects(context: Context, source, input):
    RequestValidator.validate_dataset_share_selector_input(input)
    dataset_uri = input.get('datasetUri')
    verify_share_uris = input.get('shareUris')
    return S3ShareService.verify_dataset_share_objects(uri=dataset_uri, share_uris=verify_share_uris)


def reapply_share_items_share_object_for_dataset(context: Context, source, datasetUri: str):
    return S3ShareService.reapply_share_items_for_dataset(uri=datasetUri)


def get_s3_consumption_data(context: Context, source, shareUri: str):
    return S3ShareService.get_s3_consumption_data(uri=shareUri)


def list_shared_databases_tables_with_env_group(context: Context, source, environmentUri: str, groupUri: str):
    return S3ShareService.list_shared_databases_tables_with_env_group(uri=environmentUri, group_uri=groupUri)


def resolve_shared_db_name(context: Context, source, **kwargs):
    return S3ShareService.resolve_shared_db_name(source.GlueDatabaseName, source.shareUri)


def list_shared_table_columns(context: Context, source, tableUri: str, shareUri: str, filter: dict):
    if source:
        tableUri = source.tableUri
    if not filter:
        filter = {}
    return S3ShareService.paginate_active_columns_for_table_share(uri=tableUri, shareUri=shareUri, filter=filter)


def list_table_data_filters_by_attached(
    context: Context, source, attachedDataFilterUri: str = None, filter: dict = None
):
    if not filter:
        filter = {'page': 1, 'pageSize': 5}
    return S3ShareService.list_table_data_filters_by_attached(uri=attachedDataFilterUri, data=filter)
