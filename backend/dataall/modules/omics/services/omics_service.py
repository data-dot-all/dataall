"""
A service layer for Omics pipelines
Central part for working with Omics workflow runs
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
from dataall.modules.omics.aws.omics_client import client
from dataall.modules.omics.db.mlstudio_repository import OmicsRepository
from dataall.modules.omics.db.models import OmicsRun
from dataall.modules.omics.services import permissions
from dataall.modules.omics.services.permissions import MANAGE_OMICS_RUNS, CREATE_OMICS_RUN
from dataall.core.permission_checker import has_resource_permission, has_tenant_permission, has_group_permission

logger = logging.getLogger(__name__)


@dataclass
class OmicsRunCreationRequest:
    """A request dataclass for Omics pipeline creation. Adds default values for missed parameters"""
    label: str
    SamlAdminGroupName: str
    environment: Dict = field(default_factory=dict)
    description: str = "No description provided"
    tags: List[str] = field(default_factory=list)
    S3InputBucket: str = "No input bucket provided"
    S3InputPrefix: str = ""
    S3OutputBucket: str = "No output bucket provided"
    S3OutputPrefix: str = ""


    @classmethod
    def from_dict(cls, env):
        """Copies only required fields from the dictionary and creates an instance of class"""
        fields = set([f.name for f in dataclasses.fields(cls)])
        return cls(**{
            k: v for k, v in env.items()
            if k in fields
        })


class OmicsService:
    """
    Encapsulate the logic of interactions with Omics pipelines.
    """

    _OMICS_RUN_RESOURCE_TYPE = "omics_run"

    @staticmethod
    @has_tenant_permission(MANAGE_OMICS_RUNS)
    @has_resource_permission(CREATE_OMICS_RUN)
    @has_group_permission(CREATE_OMICS_RUN)
    def CREATE_OMICS_RUN(*, uri: str, admin_group: str, request: OmicsRunCreationRequest) -> OmicsRun:
        """
        Creates an omics_run and attach policies to it
        Throws an exception if omics_run are not enabled for the environment
        """

        with _session() as session:
            environment = Environment.get_environment_by_uri(session, uri)
            enabled = EnvironmentParameterRepository(session).get_param(uri, "omicsEnabled")

            if not enabled and enabled.lower() != "true":
                raise exceptions.UnauthorizedOperation(
                    action=CREATE_OMICS_RUN,
                    message=f'OMICS_RUN feature is disabled for the environment {environment.label}',
                )

            env_group = request.environment
            if not env_group:
                env_group = Environment.get_environment_group(
                    session,
                    group_uri=admin_group,
                    environment_uri=environment.environmentUri,
                )

            omics_run = OmicsRun(
                owner=context().username,
                organizationUri=environment.organizationUri,
                environmentUri=environment.environmentUri,
                SamlAdminGroupName=admin_group,
                label=request.label,
                description=request.description,
                tags=request.tags,
                AwsAccountId=environment.AwsAccountId,
                region=environment.region,
                ## TODO: define inputs, based on resolver and on RDS table
            )

            OmicsRepository(session).save_omics_run(omics_run)


            ResourcePolicy.attach_resource_policy(
                session=session,
                group=request.SamlAdminGroupName,
                permissions=permissions.OMICS_RUN_ALL,
                resource_uri=omics_run.runUri,
                resource_type=OmicsRun.__name__,
            )

            if environment.SamlGroupName != admin_group:
                ResourcePolicy.attach_resource_policy(
                    session=session,
                    group=environment.SamlGroupName,
                    permissions=permissions.OMICS_RUN_ALL,
                    resource_uri=omics_run.runUri,
                    resource_type=OmicsRun.__name__,
                )
            ## TODO: do we need to create and deploy a stack??
            Stack.create_stack(
                session=session,
                environment_uri=omics_run.environmentUri,
                target_type='omics_run',
                target_uri=omics_run.runUri,
                target_label=omics_run.label,
            )

        stack_helper.deploy_stack(targetUri=omics_run.runUri)

        return omics_run

    @staticmethod
    def list_user_omics_runs(filter) -> dict:
        """List existed user Omics pipelines. Filters only required omics_runs by the filter param"""
        with _session() as session:
            return OmicsRepository(session).paginated_user_runs(
                username=context().username,
                groups=context().groups,
                filter=filter
            )


    @staticmethod
    @has_resource_permission(permissions.DELETE_OMICS_RUN)
    def delete_omics_run(*, uri: str, delete_from_aws: bool):
        ##T TODO: IMPLEMENT IN omics_repository
        """Deletes Omics project from the database and if delete_from_aws is True from AWS as well"""
        with _session() as session:
            omics_run = OmicsRepository(session).find_omics_run(uri)
            if not omics_run:
                raise exceptions.ObjectNotFound("OmicsRun", uri)
            KeyValueTag.delete_key_value_tags(session, omics_run.runUri, 'omics_run')
            session.delete(omics_run)

            ResourcePolicy.delete_resource_policy(
                session=session,
                resource_uri=omics_run.runUri,
                group=omics_run.SamlAdminGroupName,
            )

            env: models.Environment = Environment.get_environment_by_uri(
                session, omics_run.environmentUri
            )

        if delete_from_aws:
            stack_helper.delete_stack(
                target_uri=uri,
                accountid=env.AwsAccountId,
                cdk_role_arn=env.CDKRoleArn,
                region=env.region
            )


def _session():
    return context().db_engine.scoped_session()
