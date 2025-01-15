import logging

from dataall.base.api.context import Context
from dataall.base.db import exceptions
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.stacks.services.stack_service import StackService
from dataall.modules.datapipelines.api.enums import DataPipelineRole
from dataall.modules.datapipelines.db.datapipelines_models import DataPipeline
from dataall.modules.datapipelines.services.datapipelines_service import DataPipelineService

log = logging.getLogger(__name__)


def _validate_creation_request(data):
    if not data:
        raise exceptions.RequiredParameter(data)
    if not data.get('environmentUri'):
        raise exceptions.RequiredParameter('environmentUri')
    if not data.get('SamlGroupName'):
        raise exceptions.RequiredParameter('group')
    if not data.get('label'):
        raise exceptions.RequiredParameter('label')


def _required_uri(uri):
    if not uri:
        raise exceptions.RequiredParameter('URI')


def create_pipeline(context: Context, source, input=None):
    _validate_creation_request(input)
    admin_group = input['SamlGroupName']
    uri = input['environmentUri']
    return DataPipelineService.create_pipeline(uri=uri, admin_group=admin_group, data=input)


def create_pipeline_environment(context: Context, source, input=None):
    admin_group = input['samlGroupName']
    uri = input['environmentUri']
    return DataPipelineService.create_pipeline_environment(uri=uri, admin_group=admin_group, data=input)


def update_pipeline(context: Context, source, DataPipelineUri: str, input: dict = None):
    _required_uri(DataPipelineUri)
    return DataPipelineService.update_pipeline(uri=DataPipelineUri, data=input)


def update_pipeline_environment(context: Context, source, input=None):
    uri = input['pipelineUri']
    _required_uri(uri)
    return DataPipelineService.update_pipeline_environment(data=input, uri=input['pipelineUri'])


def delete_pipeline(context: Context, source, DataPipelineUri: str = None, deleteFromAWS: bool = None):
    _required_uri(DataPipelineUri)
    return DataPipelineService.delete_pipeline(uri=DataPipelineUri, deleteFromAWS=deleteFromAWS)


def delete_pipeline_environment(context: Context, source, envPipelineUri: str = None):
    _required_uri(envPipelineUri)
    return DataPipelineService.delete_pipeline_environment(envPipelineUri=envPipelineUri)


def list_pipelines(context: Context, source, filter: dict = None):
    if not filter:
        filter = {}
    return DataPipelineService.list_pipelines(filter=filter)


def get_pipeline(context: Context, source, DataPipelineUri: str = None):
    _required_uri(DataPipelineUri)
    return DataPipelineService.get_pipeline(uri=DataPipelineUri)


def get_creds_linux(context: Context, source, DataPipelineUri: str = None):
    _required_uri(DataPipelineUri)
    return DataPipelineService.get_credentials(uri=DataPipelineUri)


def resolve_pipeline_environments(context: Context, source: DataPipeline, filter: dict = None):
    uri = source.DataPipelineUri
    if not filter:
        filter = {}
    return DataPipelineService.list_pipeline_environments(uri=uri, filter=filter)


def resolve_user_role(context: Context, source: DataPipeline):
    if not source:
        return None
    if context.username and source.owner == context.username:
        return DataPipelineRole.Creator.value
    elif context.groups and source.SamlGroupName in context.groups:
        return DataPipelineRole.Admin.value
    return DataPipelineRole.NoPermission.value


def resolve_clone_url_http(context: Context, source: DataPipeline, **kwargs):
    if not source:
        return None
    return DataPipelineService.get_clone_url_http(uri=source.DataPipelineUri)


def resolve_stack(context, source: DataPipeline, **kwargs):
    if not source:
        return None
    return StackService.resolve_parent_obj_stack(
        targetUri=source.DataPipelineUri,
        targetType='pipeline',
        environmentUri=source.environmentUri,
    )
