#
# (c) 2020 Amazon Web Services, Inc. or its affiliates. All Rights Reserved.
# This AWS Content is provided subject to the terms of the AWS Customer
# Agreement available at http://aws.amazon.com/agreement or other
# written agreement between Customer and Amazon Web Services, Inc.
#
import logging

from sqlalchemy import or_ # type: ignore comment
from sqlalchemy.orm import Query # type: ignore comment

from dataall import addons
from dataall.db import models, exceptions, paginate, permissions
from dataall.db.api import (
    Environment,
    has_tenant_perm,
    has_resource_perm,
    ResourcePolicy,
    Dataset,
)
from dataall.utils.naming_convention import NamingConventionService, NamingConventionPattern

logger = logging.getLogger(__name__)


class OmicsPipeline:
    @staticmethod
    @has_tenant_perm(permissions.MANAGE_OMICS_PIPELINES)
    @has_resource_perm(permissions.CREATE_OMICS_PIPELINE)
    def create_pipeline(
        session,
        username: str,
        groups: [str], # type: ignore comment
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ) -> addons.models.OmicsPipeline:

        OmicsPipeline._validate_input(data)

        OmicsPipeline.validate_group_membership(
            session=session,
            username=username,
            groups=groups,
            group=data["SamlGroupName"],
            environment_uri=uri,
        )

        environment = Environment.get_environment_by_uri(session, uri)

        pipeline: addons.models.OmicsPipeline = addons.models.OmicsPipeline(
            owner=username,
            organizationUri=environment.organizationUri,
            environmentUri=environment.environmentUri,
            SamlGroupName=data["SamlGroupName"],
            label=data["label"],
            description=data.get("description", ""),
            tags=data.get("tags", []),
            AwsAccountId=environment.AwsAccountId,
            region=environment.region,
            S3InputBucket=data["S3InputBucket"],
            S3InputPrefix=data["S3InputPrefix"],
            S3OutputBucket=data["S3OutputBucket"],
            S3OutputPrefix=data["S3OutputPrefix"],
        )
        session.add(pipeline)
        session.commit()

        aws_resources_name = f"{environment.resourcePrefix}-omics-{pipeline.OmicsPipelineUri}"[:63]

        pipeline.CodeRepository = aws_resources_name
        pipeline.StepFunction = aws_resources_name
        pipeline.CiPipeline = aws_resources_name
        pipeline.OmicsWorkflow = aws_resources_name

        activity = models.Activity(
            action="OMICS_PIPELINE:CREATE",
            label="OMICS_PIPELINE:CREATE",
            owner=username,
            summary=f"{username} created OMICS_PIPELINE {pipeline.label} in {environment.label}",
            targetUri=pipeline.OmicsPipelineUri,
            targetType="OMICS_PIPELINE",
        )
        session.add(activity)

        ResourcePolicy.attach_resource_policy(
            session=session,
            group=data["SamlGroupName"],
            permissions=permissions.OMICS_PIPELINE_ALL,
            resource_uri=pipeline.OmicsPipelineUri,
            resource_type=addons.models.OmicsPipeline.__name__,
        )

        if environment.SamlGroupName != pipeline.SamlGroupName:
            ResourcePolicy.attach_resource_policy(
                session=session,
                group=environment.SamlGroupName,
                permissions=permissions.OMICS_PIPELINE_ALL,
                resource_uri=pipeline.OmicsPipelineUri,
                resource_type=addons.models.OmicsPipeline.__name__,
            )

        return pipeline

    @staticmethod
    def _validate_input(data):
        if not data:
            raise exceptions.RequiredParameter(data)
        if not data.get("environmentUri"):
            raise exceptions.RequiredParameter("environmentUri")
        if not data.get("SamlGroupName"):
            raise exceptions.RequiredParameter("group")
        if not data.get("label"):
            raise exceptions.RequiredParameter("label")
        if not data.get("S3InputBucket"):
            raise exceptions.RequiredParameter("S3InputBucket")
        if not data.get("S3OutputBucket"):
            raise exceptions.RequiredParameter("S3OutputBucket")
        if not data.get("S3InputPrefix"):
            raise exceptions.RequiredParameter("S3InputPrefix")
        if not data.get("S3OutputPrefix"):
            raise exceptions.RequiredParameter("S3OutputPrefix")

    @staticmethod
    def validate_group_membership(session, environment_uri, group, username, groups):
        if group and group not in groups:
            raise exceptions.UnauthorizedOperation(
                action=permissions.CREATE_OMICS_PIPELINE,
                message=f"User: {username} is not a member of the team {group}",
            )
        if group not in Environment.list_environment_groups(
            session=session,
            username=username,
            groups=groups,
            uri=environment_uri,
            data=None,
            check_perm=True,
        ):
            raise exceptions.UnauthorizedOperation(
                action=permissions.CREATE_OMICS_PIPELINE,
                message=f"Team: {group} is not a member of the environment {environment_uri}",
            )

    @staticmethod
    def _validate_datasets(environment, input_dataset, output_dataset):
        if not input_dataset:
            raise exceptions.ObjectNotFound(type="Dataset", id=input_dataset.datasetUri)
        if not output_dataset:
            raise exceptions.ObjectNotFound(type="Dataset", id=output_dataset.datasetUri)
        if not input_dataset.environmentUri != environment.environmentUri:
            raise exceptions.EnvironmentResourcesFound(
                action=permissions.CREATE_OMICS_PIPELINE,
                message=f"Dataset: {input_dataset.datasetUri} is not part of the environment {environment.environmentUri}.",
            )
        if not output_dataset.environmentUri != environment.environmentUri:
            raise exceptions.EnvironmentResourcesFound(
                action=permissions.CREATE_OMICS_PIPELINE,
                message=f"Dataset: {output_dataset.datasetUri} is not part of the environment {environment.environmentUri}.",
            )

    @staticmethod
    @has_tenant_perm(permissions.MANAGE_OMICS_PIPELINES)
    @has_resource_perm(permissions.GET_OMICS_PIPELINE)
    def get_instance(
        session,
        username: str,
        groups: [str], # type: ignore comment
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ) -> addons.models.OmicsPipeline:
        return OmicsPipeline.get_pipeline_by_uri(session, uri)

    @staticmethod
    @has_tenant_perm(permissions.MANAGE_OMICS_PIPELINES)
    @has_resource_perm(permissions.UPDATE_OMICS_PIPELINE)
    def update_pipeline(session, username, groups, uri, data=None, check_perm=None) -> addons.models.OmicsPipeline:
        pipeline: addons.models.OmicsPipeline = OmicsPipeline.get_pipeline_by_uri(session, uri)
        if data:
            if isinstance(data, dict):
                for k in data.keys():
                    setattr(pipeline, k, data.get(k))
        return pipeline

    @staticmethod
    def get_pipeline_by_uri(session, uri):
        pipeline: addons.models.OmicsPipeline = session.query(addons.models.OmicsPipeline).get(uri)
        if not pipeline:
            raise exceptions.ObjectNotFound("OmicsPipeline", uri)
        return pipeline

    @staticmethod
    def query_user_pipelines(session, username, groups, filter) -> Query:
        query = session.query(addons.models.OmicsPipeline).filter(
            or_(
                addons.models.OmicsPipeline.owner == username,
                addons.models.OmicsPipeline.SamlGroupName.in_(groups),
            )
        )
        if filter and filter.get("term"):
            query = query.filter(
                or_(
                    addons.models.OmicsPipeline.description.ilike(filter.get("term") + "%%"),
                    addons.models.OmicsPipeline.label.ilike(filter.get("term") + "%%"),
                )
            )
        return query

    @staticmethod
    def paginated_user_instances(session, username, groups, uri, data=None, check_perm=None) -> dict:
        return paginate(
            query=OmicsPipeline.query_user_pipelines(session, username, groups, data),
            page=data.get("page", 1),
            page_size=data.get("pageSize", 10),
        ).to_dict()

    @staticmethod
    @has_tenant_perm(permissions.MANAGE_OMICS_PIPELINES)
    @has_resource_perm(permissions.DELETE_OMICS_PIPELINE)
    def delete(session, username, groups, uri, data=None, check_perm=None) -> bool:
        pipeline = data.get("pipeline", OmicsPipeline.get_pipeline_by_uri(session, uri))
        session.delete(pipeline)
        ResourcePolicy.delete_resource_policy(session=session, resource_uri=uri, group=pipeline.SamlGroupName)
        session.commit()
        return True