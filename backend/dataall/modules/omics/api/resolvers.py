from dataall.modules.omics.api.enums import OmicsProjectRole

from dataall.api.context import Context
from dataall.db import exceptions
from dataall.api.Objects.Stack import stack_helper
from dataall.modules.omics.services.services import OmicsService, OmicsProjectCreationRequest
from dataall.modules.omics.db.models import OmicsProject


def create_omics_project(context: Context, source: OmicsProject, input: dict = None):
    """Creates an Omics Project. Deploys the omics project stack into AWS"""
    RequestValidator.validate_creation_request(input)
    request = OmicsProjectCreationRequest.from_dict(input)
    return OmicsService.create_omics_project(
        uri=input["environmentUri"],
        admin_group=input["SamlAdminGroupName"],
        request=request
    )


def list_omics_projects(context, source, filter: dict = None):
    """
    Lists all Omics Projects using the given filter.
    If the filter is not provided, all projects are returned.
    """

    if not filter:
        filter = {}
    return OmicsService.list_user_omics_projects(filter)


def get_omics_project(context, source, projectUri: str = None):
    """Retrieve a Omics project by URI."""
    RequestValidator.required_uri(projectUri)
    return OmicsService.get_omics_project(uri=projectUri)



def delete_omics_project(
    context,
    source: OmicsProject,
    projectUri: str = None,
    deleteFromAWS: bool = None,
):
    """
    Deletes the Omics project.
    Deletes the omics projects stack from AWS if deleteFromAWS is True
    """
    RequestValidator.required_uri(projectUri)
    OmicsService.delete_omics_project(uri=projectUri, delete_from_aws=deleteFromAWS)
    return True


def resolve_user_role(context: Context, source: OmicsProject):
    if not source:
        return None
    if source.owner == context.username:
        return OmicsProjectRole.CREATOR.value
    elif context.groups and source.SamlAdminGroupName in context.groups:
        return OmicsProjectRole.ADMIN.value
    return OmicsProjectRole.NO_PERMISSION.value


def resolve_omics_stack(context: Context, source: OmicsProject, **kwargs):
    if not source:
        return None
    return stack_helper.get_stack_with_cfn_resources(
        targetUri=source.projectUri,
        environmentUri=source.environmentUri,
    )


class RequestValidator:
    """Aggregates all validation logic for operating with omics projects"""
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
