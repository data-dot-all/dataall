import logging
from dataall.base.api.context import Context
from dataall.base.db import exceptions
from dataall.modules.omics.services.omics_service import OmicsService
from dataall.modules.omics.db.omics_models import OmicsRun

log = logging.getLogger(__name__)


class RequestValidator:
    """Aggregates all validation logic for operating with omics"""

    @staticmethod
    def required_uri(uri):
        if not uri:
            raise exceptions.RequiredParameter('URI')

    @staticmethod
    def validate_creation_request(data):
        required = RequestValidator._required
        if not data:
            raise exceptions.RequiredParameter('data')
        if not data.get('label'):
            raise exceptions.RequiredParameter('name')

        required(data, 'environmentUri')
        required(data, 'SamlAdminGroupName')
        required(data, 'workflowUri')
        required(data, 'parameterTemplate')
        required(data, 'destination')

    @staticmethod
    def _required(data: dict, name: str):
        if not data.get(name):
            raise exceptions.RequiredParameter(name)


def create_omics_run(context: Context, source, input=None):
    RequestValidator.validate_creation_request(input)
    return OmicsService.create_omics_run(
        uri=input['environmentUri'], admin_group=input['SamlAdminGroupName'], data=input
    )


def list_omics_runs(context: Context, source, filter: dict = None):
    if not filter:
        filter = {}
    return OmicsService.list_user_omics_runs(filter)


def list_omics_workflows(context: Context, source, filter: dict = None):
    if not filter:
        filter = {}
    return OmicsService.list_omics_workflows(filter)


def get_omics_workflow(context: Context, source, workflowUri: str = None):
    RequestValidator.required_uri(workflowUri)
    return OmicsService.get_omics_workflow(workflowUri)


def delete_omics_run(context: Context, source, input):
    RequestValidator.required_uri(input.get('runUris'))
    return OmicsService.delete_omics_runs(uris=input.get('runUris'), delete_from_aws=input.get('deleteFromAWS', True))


def resolve_omics_workflow(context, source: OmicsRun, **kwargs):
    if not source:
        return None
    return OmicsService.get_omics_workflow(source.workflowUri)


def resolve_omics_run_details(context, source: OmicsRun, **kwargs):
    if not source:
        return None
    return OmicsService.get_omics_run_details_from_aws(source.runUri)
