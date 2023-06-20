"""
A service layer for Omics pipelines
Central part for working with Omics pipelines
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
from dataall.modules.omics.db.mlstudio_repository import OmicsPipelineRepository
from dataall.modules.omics.db.models import OmicsPipeline
from dataall.modules.omics.services import permissions
from dataall.modules.omics.services.permissions import MANAGE_OMICS_PIPELINES, CREATE_OMICS_PIPELINE
from dataall.core.permission_checker import has_resource_permission, has_tenant_permission, has_group_permission

logger = logging.getLogger(__name__)


@dataclass
class OmicsPipelineCreationRequest:
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


class OmicsPipelineService:
    """
    Encapsulate the logic of interactions with Omics pipelines.
    """

    _OMICS_PIPELINE_RESOURCE_TYPE = "omics_pipeline"

    @staticmethod
    @has_tenant_permission(MANAGE_OMICS_PIPELINES)
    @has_resource_permission(CREATE_OMICS_PIPELINE)
    @has_group_permission(CREATE_OMICS_PIPELINE)
    def create_omics_pipeline(*, uri: str, admin_group: str, request: OmicsPipelineCreationRequest) -> OmicsPipeline:
        """
        Creates an omics_pipeline and attach policies to it
        Throws an exception if omics_pipeline are not enabled for the environment
        """

        with _session() as session:
            environment = Environment.get_environment_by_uri(session, uri)
            enabled = EnvironmentParameterRepository(session).get_param(uri, "omicsEnabled")

            if not enabled and enabled.lower() != "true":
                raise exceptions.UnauthorizedOperation(
                    action=CREATE_OMICS_PIPELINE,
                    message=f'OMICS_PIPELINE feature is disabled for the environment {environment.label}',
                )

            env_group = request.environment
            if not env_group:
                env_group = Environment.get_environment_group(
                    session,
                    group_uri=admin_group,
                    environment_uri=environment.environmentUri,
                )

            omics_pipeline = OmicsPipeline(
                owner=context().username,
                organizationUri=environment.organizationUri,
                environmentUri=environment.environmentUri,
                SamlAdminGroupName=admin_group,
                label=request.label,
                description=request.description,
                tags=request.tags,
                AwsAccountId=environment.AwsAccountId,
                region=environment.region,
                S3InputBucket=request.S3InputBucket,
                S3InputPrefix=request.S3InputPrefix,
                S3OutputBucket=request.S3OutputBucket,
                S3OutputPrefix=request.S3OutputPrefix,
            )

            OmicsPipelineRepository(session).save_omics_pipeline(omics_pipeline)


            ResourcePolicy.attach_resource_policy(
                session=session,
                group=request.SamlAdminGroupName,
                permissions=permissions.OMICS_PIPELINE_ALL,
                resource_uri=omics_pipeline.OmicsPipelineUri,
                resource_type=OmicsPipeline.__name__,
            )

            if environment.SamlGroupName != admin_group:
                ResourcePolicy.attach_resource_policy(
                    session=session,
                    group=environment.SamlGroupName,
                    permissions=permissions.OMICS_PIPELINE_ALL,
                    resource_uri=omics_pipeline.OmicsPipelineUri,
                    resource_type=OmicsPipeline.__name__,
                )

            Stack.create_stack(
                session=session,
                environment_uri=omics_pipeline.environmentUri,
                target_type='omics_pipeline',
                target_uri=omics_pipeline.OmicsPipelineUri,
                target_label=omics_pipeline.label,
            )

        stack_helper.deploy_stack(targetUri=omics_pipeline.OmicsPipelineUri)

        return omics_pipeline

    @staticmethod
    def list_user_omics_pipelines(filter) -> dict:
        """List existed user Omics pipelines. Filters only required omics_pipelines by the filter param"""
        with _session() as session:
            return OmicsPipelineRepository(session).paginated_user_omics_pipelines(
                username=context().username,
                groups=context().groups,
                filter=filter
            )

    @staticmethod
    @has_resource_permission(permissions.GET_OMICS_PIPELINE)
    def get_omics_pipeline(*, uri) -> OmicsPipeline:
        """Gets a Omics project by uri"""
        with _session() as session:
            omics_pipeline = OmicsPipelineRepository(session).find_omics_pipeline(uri)
            if not omics_pipeline:
                raise exceptions.ObjectNotFound("OmicsPipeline", uri)
            return omics_pipeline

    @staticmethod
    @has_resource_permission(permissions.DELETE_OMICS_PIPELINE)
    def delete_omics_pipeline(*, uri: str, delete_from_aws: bool):
        """Deletes Omics project from the database and if delete_from_aws is True from AWS as well"""
        with _session() as session:
            omics_pipeline = OmicsPipelineRepository(session).find_omics_pipeline(uri)
            if not omics_pipeline:
                raise exceptions.ObjectNotFound("OmicsPipeline", uri)
            KeyValueTag.delete_key_value_tags(session, omics_pipeline.OmicsPipelineUri, 'omics_pipeline')
            session.delete(omics_pipeline)

            ResourcePolicy.delete_resource_policy(
                session=session,
                resource_uri=omics_pipeline.OmicsPipelineUri,
                group=omics_pipeline.SamlAdminGroupName,
            )

            env: models.Environment = Environment.get_environment_by_uri(
                session, omics_pipeline.environmentUri
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
