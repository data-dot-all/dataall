import logging
from dataall.base.api.context import Context
from dataall.core.stacks.api import stack_helper
from dataall.base.db import exceptions
from dataall.modules.omics.api.enums import OmicsRunRole
from dataall.modules.omics.services.omics_service import OmicsService, OmicsRunCreationRequest
from dataall.modules.omics.db.models import OmicsRun, OmicsWorkflow

log = logging.getLogger(__name__)

## TODO: it is very incomplete but can serve as starting point
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

        required(data, "environmentUri")
        required(data, "SamlAdminGroupName")

    @staticmethod
    def _required(data: dict, name: str):
        if not data.get(name):
            raise exceptions.RequiredParameter(name)

def create_omics_run(context: Context, source, input=None):
    RequestValidator.validate_creation_request(input)
    # request = OmicsRunCreationRequest.from_dict(input)
    return OmicsService.create_omics_run(
        uri=input["environmentUri"],
        admin_group=input["SamlAdminGroupName"],
        data=input
    )


def list_omics_runs(context: Context, source, filter: dict = None):
    if not filter:
        filter = {}
    return OmicsService.list_user_omics_runs(filter)


def list_omics_workflows(context: Context, source, filter: dict = None):
    if not filter:
        filter = {}
    return OmicsService.list_omics_workflows(filter)


def get_omics_workflow(context: Context, source, workflowId: str = None):
    print('**** WorkflowId: ', workflowId)
    RequestValidator.required_uri(workflowId)
    return OmicsService.get_omics_workflow(workflowId)

def run_omics_workflow(context: Context, source, workflowId: str = None, workflowType: str = 'READY2RUN', roleArn: str = None, parameters: str = None):
    print('**** WorkflowId: ', workflowId)
    RequestValidator.required_uri(workflowId)
    return OmicsService.run_omics_workflow(workflowId,workflowType,roleArn,parameters)

def delete_omics_run(context: Context, source, runUri: str = None, deleteFromAWS: bool = None):
    RequestValidator.required_uri(runUri)
    return OmicsService.delete_omics_run(
        uri=runUri,
        delete_from_aws=deleteFromAWS
    )

def resolve_omics_workflow(context, source: OmicsRun, **kwargs):
    return OmicsService.get_omics_workflow(source.workflowId)


def resolve_omics_run_details(context, source: OmicsRun, **kwargs):
    return OmicsService.get_omics_run_from_aws(source.runUri)


