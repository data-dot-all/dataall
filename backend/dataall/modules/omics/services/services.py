"""
A service layer for omics projects
Central part for working with omics projects
"""
import contextlib
import dataclasses
import logging
from dataclasses import dataclass, field
from typing import List, Dict

from dataall.api.Objects.Stack import stack_helper
from dataall.core.context import get_context as context
from dataall.core.environment.db.repositories import EnvironmentParameterRepository
from dataall.db.api import (
    ResourcePolicy,
    Environment, KeyValueTag, Stack,
)
from dataall.db import models, exceptions
from dataall.modules.omics.aws.client import client
from dataall.modules.omics.db.repositories import OmicsProjectRepository
from dataall.utils.naming_convention import (
    NamingConventionService,
    NamingConventionPattern,
)
from dataall.utils.slugify import slugify
from dataall.modules.omics.db.models import OmicsProject
from dataall.modules.omics.services import permissions
from dataall.modules.omics.services.permissions import MANAGE_OMICS_PROJECTS, CREATE_OMICS_PROJECT
from dataall.core.permission_checker import has_resource_permission, has_tenant_permission, has_group_permission

logger = logging.getLogger(__name__)


@dataclass
class OmicsProjectCreationRequest:
    """A request dataclass for omics project creation. Adds default values for missed parameters"""
    label: str
    SamlAdminGroupName: str
    environment: Dict = field(default_factory=dict)
    description: str = "No description provided"
    tags: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, env):
        """Copies only required fields from the dictionary and creates an instance of class"""
        fields = set([f.name for f in dataclasses.fields(cls)])
        return cls(**{
            k: v for k, v in env.items()
            if k in fields
        })


class OmicsProjectService:
    """
    Encapsulate the logic of interactions with omics projects.
    """

    _OMICS_PROJECT_RESOURCE_TYPE = "omics_project"

    @staticmethod
    @has_tenant_permission(MANAGE_OMICS_PROJECTS)
    @has_resource_permission(CREATE_OMICS_PROJECT)
    @has_group_permission(CREATE_OMICS_PROJECT)
    def create_omics_project(*, uri: str, admin_group: str, request: OmicsProjectCreationRequest) -> OmicsProject:
        """
        Creates a omics_project and attach policies to it
        Throws an exception if omics_project are not enabled for the environment
        """

        with _session() as session:
            env = Environment.get_environment_by_uri(session, uri)
            enabled = EnvironmentParameterRepository(session).get_param(uri, "omicsEnabled")

            if not enabled and enabled.lower() != "true":
                raise exceptions.UnauthorizedOperation(
                    action=CREATE_OMICS_PROJECT,
                    message=f'OMICS_PROJECT feature is disabled for the environment {env.label}',
                )

            env_group = request.environment
            if not env_group:
                env_group = Environment.get_environment_group(
                    session,
                    group_uri=admin_group,
                    environment_uri=env.environmentUri,
                )

            omics_project = OmicsProject(
                label=request.label,
                environmentUri=env.environmentUri,
                description=request.description,
                AWSAccountId=env.AwsAccountId,
                region=env.region,
                owner=context().username,
                SamlAdminGroupName=admin_group,
                tags=request.tags,
            )

            OmicsProjectRepository(session).save_omics_project(omics_project)


            ResourcePolicy.attach_resource_policy(
                session=session,
                group=request.SamlAdminGroupName,
                permissions=permissions.OMICS_PROJECT_ALL,
                resource_uri=omics_project.projectUri,
                resource_type=OmicsProject.__name__,
            )

            if env.SamlGroupName != admin_group:
                ResourcePolicy.attach_resource_policy(
                    session=session,
                    group=env.SamlGroupName,
                    permissions=permissions.OMICS_PROJECT_ALL,
                    resource_uri=omics_project.projectUri,
                    resource_type=OmicsProject.__name__,
                )

            Stack.create_stack(
                session=session,
                environment_uri=omics_project.environmentUri,
                target_type='omics_project',
                target_uri=omics_project.projectUri,
                target_label=omics_project.label,
            )

        stack_helper.deploy_stack(targetUri=omics_project.projectUri)

        return omics_project

    @staticmethod
    def list_user_omics_projects(filter) -> dict:
        """List existed user omics projects. Filters only required omics_projects by the filter param"""
        with _session() as session:
            return OmicsProjectRepository(session).paginated_user_omics_projects(
                username=context().username,
                groups=context().groups,
                filter=filter
            )

    @staticmethod
    @has_resource_permission(permissions.GET_OMICS_PROJECT)
    def get_omics_project(*, uri) -> OmicsProject:
        """Gets a omics project by uri"""
        with _session() as session:
            return OmicsProjectService._get_omics_project(session, uri)

    @staticmethod
    @has_resource_permission(permissions.DELETE_OMICS_PROJECT)
    def delete_omics_project(*, uri: str, delete_from_aws: bool):
        """Deletes omics project from the database and if delete_from_aws is True from AWS as well"""
        with _session() as session:
            omics_project = OmicsProjectService._get_omics_project(session, uri)
            KeyValueTag.delete_key_value_tags(session, omics_project.projectUri, 'omics_project')
            session.delete(omics_project)

            ResourcePolicy.delete_resource_policy(
                session=session,
                resource_uri=omics_project.projectUri,
                group=omics_project.SamlAdminGroupName,
            )

            env: models.Environment = Environment.get_environment_by_uri(
                session, omics_project.environmentUri
            )

        if delete_from_aws:
            stack_helper.delete_stack(
                target_uri=uri,
                accountid=env.AwsAccountId,
                cdk_role_arn=env.CDKRoleArn,
                region=env.region
            )

    @staticmethod
    def _get_omics_project(session, uri) -> OmicsProject:
        omics_project = OmicsProjectRepository(session).find_omics_project(uri)

        if not omics_project:
            raise exceptions.ObjectNotFound('OMICS_PROJECT', uri)
        return omics_project


def _session():
    return context().db_engine.scoped_session()
