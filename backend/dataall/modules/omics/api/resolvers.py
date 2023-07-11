import logging

from dataall.db import exceptions
from dataall.modules.omics.api.enums import OmicsRunRole
from dataall.modules.omics.services.omics_service import OmicsService, OmicsRunCreationRequest
from dataall.modules.omics.db.models import OmicsRun, OmicsWorkflow
from dataall.api.Objects.Stack import stack_helper
from dataall.api.Objects.Stack.stack_helper import deploy_stack
from dataall.api.context import Context
from dataall.db import models, permissions
from dataall.db.api import Environment, ResourcePolicy, Organization

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
    request = OmicsRunCreationRequest.from_dict(input)
    return OmicsService.create_omics_run(
        uri=input["environmentUri"],
        admin_group=input["SamlAdminGroupName"],
        request=request
    )


# def update_omics_pipeline(context: Context, source, OmicsPipelineUri: str, input: dict = None):
#     RequestValidator.required_uri(OmicsPipelineUri)
#     return OmicsPipelineService.update_omics_pipeline(OmicsPipelineUri, input)


def list_runs(context: Context, source, filter: dict = None):
    if not filter:
        filter = {}
    return OmicsService.list_user_runs(filter)


def list_workflows(context: Context, source, filter: dict = None):
    if not filter:
        filter = {}
    return OmicsService.list_workflows(filter)

def get_omics_workflow(context: Context, source, workflowUri: str = None):
    RequestValidator.required_uri(workflowUri)
    return OmicsService.get_omics_workflow(workflowUri)



def delete_omics_run(context: Context, source, runUri: str = None, deleteFromAWS: bool = None):
    RequestValidator.required_uri(runUri)
    return OmicsService.delete_omics_run(
        uri=runUri,
        delete_from_aws=deleteFromAWS
    )


def resolve_user_role(context: Context, source: OmicsRun):
    if context.username and source.owner == context.username:
        return OmicsRunRole.Creator.value
    elif context.groups and source.SamlGroupName in context.groups:
        return OmicsRunRole.Admin.value
    return OmicsRunRole.NoPermission.value


def resolve_omics_run_stack(context, source: OmicsRun, **kwargs):
    return stack_helper.get_stack_with_cfn_resources(
        targetUri=source.runUri,
        environmentUri=source.environmentUri,
    )


