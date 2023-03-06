"""
A service layer for sagemaker notebooks
Central part for working with notebooks
"""
import contextlib
import dataclasses
import logging
from dataclasses import dataclass, field
from typing import List, Dict

from dataall.api.Objects.Stack import stack_helper
from dataall.core.context import get_context as context
from dataall.core.environment.db.repositories import EnvironmentResourceRepository, EnvironmentParameterRepository
from dataall.db.api import (
    ResourcePolicy,
    Environment, KeyValueTag, Stack,
)
from dataall.db import models, exceptions
from dataall.modules.notebooks.aws.client import client
from dataall.modules.notebooks.db.repositories import NotebookRepository
from dataall.utils.naming_convention import (
    NamingConventionService,
    NamingConventionPattern,
)
from dataall.utils.slugify import slugify
from dataall.modules.notebooks.db.models import SagemakerNotebook
from dataall.modules.notebooks.services import permissions
from dataall.modules.common.sagemaker.permissions import MANAGE_NOTEBOOKS, CREATE_NOTEBOOK
from dataall.core.permission_checker import has_resource_permission, has_tenant_permission, has_group_permission

logger = logging.getLogger(__name__)


@dataclass
class NotebookCreationRequest:
    """A request dataclass for notebook creation. Adds default values for missed parameters"""
    label: str
    VpcId: str
    SubnetId: str
    SamlAdminGroupName: str
    environment: Dict = field(default_factory=dict)
    description: str = "No description provided"
    VolumeSizeInGB: int = 32
    InstanceType: str = "ml.t3.medium"
    tags: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, env):
        """Copies only required fields from the dictionary and creates an instance of class"""
        fields = set([f.name for f in dataclasses.fields(cls)])
        return cls(**{
            k: v for k, v in env.items()
            if k in fields
        })


class NotebookService:
    """
    Encapsulate the logic of interactions with sagemaker notebooks.
    """

    _NOTEBOOK_RESOURCE_TYPE = "notebook"

    @staticmethod
    @has_tenant_permission(MANAGE_NOTEBOOKS)
    @has_resource_permission(CREATE_NOTEBOOK)
    @has_group_permission(CREATE_NOTEBOOK)
    def create_notebook(*, uri: str, admin_group: str, request: NotebookCreationRequest) -> SagemakerNotebook:
        """
        Creates a notebook and attach policies to it
        Throws an exception if notebook are not enabled for the environment
        """

        with _session() as session:
            env = Environment.get_environment_by_uri(session, uri)
            enabled = EnvironmentParameterRepository(session).get_param(uri, "notebooksEnabled")

            if not enabled and enabled.lower() != "true":
                raise exceptions.UnauthorizedOperation(
                    action=CREATE_NOTEBOOK,
                    message=f'Notebooks feature is disabled for the environment {env.label}',
                )

            env_group = request.environment
            if not env_group:
                env_group = Environment.get_environment_group(
                    session,
                    group_uri=admin_group,
                    environment_uri=env.environmentUri,
                )

            notebook = SagemakerNotebook(
                label=request.label,
                environmentUri=env.environmentUri,
                description=request.description,
                NotebookInstanceName=slugify(request.label, separator=''),
                NotebookInstanceStatus='NotStarted',
                AWSAccountId=env.AwsAccountId,
                region=env.region,
                RoleArn=env_group.environmentIAMRoleArn,
                owner=context().username,
                SamlAdminGroupName=admin_group,
                tags=request.tags,
                VpcId=request.VpcId,
                SubnetId=request.SubnetId,
                VolumeSizeInGB=request.VolumeSizeInGB,
                InstanceType=request.InstanceType,
            )

            NotebookRepository(session).save_notebook(notebook)

            # Creates a record that environment resources has been created
            EnvironmentResourceRepository(session).create(
                environment_uri=notebook.environmentUri,
                resource_uri=notebook.notebookUri,
                resource_type=NotebookService._NOTEBOOK_RESOURCE_TYPE
            )

            notebook.NotebookInstanceName = NamingConventionService(
                target_uri=notebook.notebookUri,
                target_label=notebook.label,
                pattern=NamingConventionPattern.NOTEBOOK,
                resource_prefix=env.resourcePrefix,
            ).build_compliant_name()

            ResourcePolicy.attach_resource_policy(
                session=session,
                group=request.SamlAdminGroupName,
                permissions=permissions.NOTEBOOK_ALL,
                resource_uri=notebook.notebookUri,
                resource_type=SagemakerNotebook.__name__,
            )

            if env.SamlGroupName != admin_group:
                ResourcePolicy.attach_resource_policy(
                    session=session,
                    group=env.SamlGroupName,
                    permissions=permissions.NOTEBOOK_ALL,
                    resource_uri=notebook.notebookUri,
                    resource_type=SagemakerNotebook.__name__,
                )

            Stack.create_stack(
                session=session,
                environment_uri=notebook.environmentUri,
                target_type='notebook',
                target_uri=notebook.notebookUri,
                target_label=notebook.label,
            )

        stack_helper.deploy_stack(targetUri=notebook.notebookUri)

        return notebook

    @staticmethod
    def list_user_notebooks(filter) -> dict:
        """List existed user notebooks. Filters only required notebooks by the filter param"""
        with _session() as session:
            return NotebookRepository(session).paginated_user_notebooks(
                username=context().username,
                groups=context().groups,
                filter=filter
            )

    @staticmethod
    @has_resource_permission(permissions.GET_NOTEBOOK)
    def get_notebook(*, uri) -> SagemakerNotebook:
        """Gets a notebook by uri"""
        with _session() as session:
            return NotebookService._get_notebook(session, uri)

    @staticmethod
    @has_resource_permission(permissions.UPDATE_NOTEBOOK)
    def start_notebook(*, uri):
        """Starts notebooks instance"""
        notebook = NotebookService.get_notebook(uri=uri)
        client(notebook).start_instance()

    @staticmethod
    @has_resource_permission(permissions.UPDATE_NOTEBOOK)
    def stop_notebook(*, uri: str) -> None:
        """Stop notebook instance"""
        notebook = NotebookService.get_notebook(uri=uri)
        client(notebook).stop_instance()

    @staticmethod
    @has_resource_permission(permissions.GET_NOTEBOOK)
    def get_notebook_presigned_url(*, uri: str) -> str:
        """Creates and returns a presigned url for a notebook"""
        notebook = NotebookService.get_notebook(uri=uri)
        return client(notebook).presigned_url()

    @staticmethod
    @has_resource_permission(permissions.GET_NOTEBOOK)
    def get_notebook_status(*, uri) -> str:
        """Retrieves notebook status"""
        return client(uri).get_notebook_instance_status()

    @staticmethod
    @has_resource_permission(permissions.DELETE_NOTEBOOK)
    def delete_notebook(*, uri: str, delete_from_aws: bool):
        """Deletes notebook from the database and if delete_from_aws is True from AWS as well"""
        with _session() as session:
            notebook = NotebookService._get_notebook(session, uri)
            KeyValueTag.delete_key_value_tags(session, notebook.notebookUri, 'notebook')

            EnvironmentResourceRepository(session).delete(
                environment_uri=notebook.environmentUri,
                resource_uri=notebook.notebookUri,
                resource_type=NotebookService._NOTEBOOK_RESOURCE_TYPE
            )
            session.delete(notebook)

            ResourcePolicy.delete_resource_policy(
                session=session,
                resource_uri=notebook.notebookUri,
                group=notebook.SamlAdminGroupName,
            )

            env: models.Environment = Environment.get_environment_by_uri(
                session, notebook.environmentUri
            )

        if delete_from_aws:
            stack_helper.delete_stack(
                target_uri=uri,
                accountid=env.AwsAccountId,
                cdk_role_arn=env.CDKRoleArn,
                region=env.region
            )

    @staticmethod
    def _get_notebook(session, uri) -> SagemakerNotebook:
        notebook = NotebookRepository(session).find_notebook(uri)

        if not notebook:
            raise exceptions.ObjectNotFound('SagemakerNotebook', uri)
        return notebook


def _session():
    return context().db_engine.scoped_session()
