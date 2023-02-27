"""A service layer for sagemaker notebooks"""
import logging

from dataall.core.context import get_context as context
from dataall.core.environment.models import EnvironmentResource
from dataall.db.api import (
    ResourcePolicy,
    Environment,
)
from dataall.db import models, exceptions
from dataall.modules.notebooks.db.repositories import NotebookRepository
from dataall.utils.naming_convention import (
    NamingConventionService,
    NamingConventionPattern,
)
from dataall.utils.slugify import slugify
from dataall.modules.notebooks.models import SagemakerNotebook
from dataall.modules.notebooks import permissions
from dataall.modules.common.sagemaker.permissions import MANAGE_NOTEBOOKS, CREATE_NOTEBOOK
from dataall.core.permission_checker import has_resource_permission, has_tenant_permission, has_group_permission

logger = logging.getLogger(__name__)


class NotebookService:
    """
    Encapsulate the logic of interactions with sagemaker notebooks.
    """

    @staticmethod
    @has_tenant_permission(MANAGE_NOTEBOOKS)
    @has_resource_permission(CREATE_NOTEBOOK)
    @has_group_permission(CREATE_NOTEBOOK)
    def create_notebook(uri, data=None) -> SagemakerNotebook:
        """
        Creates a notebook and attach policies to it
        Throws an exception if notebook are not enabled for the environment
        """

        with NotebookService._session() as session:
            NotebookService._validate_params(data)
            env = Environment.get_environment_by_uri(session, uri)

            if not bool(env.get_param("notebooksEnabled", False)):
                raise exceptions.UnauthorizedOperation(
                    action=CREATE_NOTEBOOK,
                    message=f'Notebooks feature is disabled for the environment {env.label}',
                )

            env_group: models.EnvironmentGroup = data.get(
                'environment',
                Environment.get_environment_group(
                    session,
                    group_uri=data['SamlAdminGroupName'],
                    environment_uri=env.environmentUri,
                ),
            )

            notebook = SagemakerNotebook(
                label=data.get('label', 'Untitled'),
                environmentUri=env.environmentUri,
                description=data.get('description', 'No description provided'),
                NotebookInstanceName=slugify(data.get('label'), separator=''),
                NotebookInstanceStatus='NotStarted',
                AWSAccountId=env.AwsAccountId,
                region=env.region,
                RoleArn=env_group.environmentIAMRoleArn,
                owner=context().username,
                SamlAdminGroupName=data.get('SamlAdminGroupName', env.SamlGroupName),
                tags=data.get('tags', []),
                VpcId=data.get('VpcId'),
                SubnetId=data.get('SubnetId'),
                VolumeSizeInGB=data.get('VolumeSizeInGB', 32),
                InstanceType=data.get('InstanceType', 'ml.t3.medium'),
            )

            NotebookRepository(session).save_notebook(notebook)

            # Creates a record that environment resources has been created
            resource = EnvironmentResource(
                environmentUri=env.environmentUri,
                resourceUri=notebook.notebookUri,
                resourceType="notebook"
            )
            session.add(resource)

            notebook.NotebookInstanceName = NamingConventionService(
                target_uri=notebook.notebookUri,
                target_label=notebook.label,
                pattern=NamingConventionPattern.NOTEBOOK,
                resource_prefix=env.resourcePrefix,
            ).build_compliant_name()

            ResourcePolicy.attach_resource_policy(
                session=session,
                group=data['SamlAdminGroupName'],
                permissions=permissions.NOTEBOOK_ALL,
                resource_uri=notebook.notebookUri,
                resource_type=SagemakerNotebook.__name__,
            )

            if env.SamlGroupName != notebook.SamlAdminGroupName:
                ResourcePolicy.attach_resource_policy(
                    session=session,
                    group=env.SamlGroupName,
                    permissions=permissions.NOTEBOOK_ALL,
                    resource_uri=notebook.notebookUri,
                    resource_type=SagemakerNotebook.__name__,
                )

            return notebook

    @staticmethod
    def _validate_params(data):
        if not data:
            raise exceptions.RequiredParameter('data')
        if not data.get('environmentUri'):
            raise exceptions.RequiredParameter('environmentUri')
        if not data.get('label'):
            raise exceptions.RequiredParameter('name')

    @staticmethod
    # TODO NO PERMISSION CHECK!
    def list_user_notebooks(filter) -> dict:
        with NotebookService._session() as session:
            return NotebookRepository(session).paginated_user_notebooks(
                username=context().username,
                groups=context().groups,
                filter=filter
            )

    @staticmethod
    @has_resource_permission(permissions.GET_NOTEBOOK)
    def get_notebook(*, uri) -> SagemakerNotebook:
        """Gets a notebook by uri"""
        if not uri:
            raise exceptions.RequiredParameter('URI')

        with NotebookService._session() as session:
            notebook = NotebookRepository(session).find_notebook(uri)

        if not notebook:
            raise exceptions.ObjectNotFound('SagemakerNotebook', uri)
        return notebook

    @staticmethod
    def _session():
        return context().db_engine.session()