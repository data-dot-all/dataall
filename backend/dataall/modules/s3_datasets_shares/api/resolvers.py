import logging

from dataall.base.api.context import Context
from dataall.base.db.exceptions import RequiredParameter
from dataall.base.feature_toggle_checker import is_feature_enabled
from dataall.modules.s3_datasets_shares.services.dataset_sharing_service import DatasetSharingService


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
    return DatasetSharingService.list_shared_tables_by_env_dataset(datasetUri, envUri)


@is_feature_enabled('modules.s3_datasets.features.aws_actions')
def get_dataset_shared_assume_role_url(context: Context, source, datasetUri: str = None):
    return DatasetSharingService.get_dataset_shared_assume_role_url(uri=datasetUri)


def verify_dataset_share_objects(context: Context, source, input):
    RequestValidator.validate_dataset_share_selector_input(input)
    dataset_uri = input.get('datasetUri')
    verify_share_uris = input.get('shareUris')
    return DatasetSharingService.verify_dataset_share_objects(uri=dataset_uri, share_uris=verify_share_uris)


def list_dataset_share_objects(context, source, filter: dict = None):
    if not source:
        return None
    if not filter:
        filter = {'page': 1, 'pageSize': 5}
    return DatasetSharingService.list_dataset_share_objects(source, filter)


def get_s3_consumption_data(context: Context, source, shareUri: str):
    return DatasetSharingService.get_s3_consumption_data(uri=shareUri)


def list_shared_databases_tables_with_env_group(context: Context, source, environmentUri: str, groupUri: str):
    return DatasetSharingService.list_shared_databases_tables_with_env_group(
        environmentUri=environmentUri, groupUri=groupUri
    )


def resolve_shared_db_name(context: Context, source, **kwargs):
    return DatasetSharingService.resolve_shared_db_name(
        source.GlueDatabaseName, source.shareUri, source.targetEnvAwsAccountId, source.targetEnvRegion
    )
