"""
DAO layer that encapsulates the logic and interaction with the database for Omics
Provides the API to retrieve / update / delete omics resources
"""
from sqlalchemy import or_
from sqlalchemy.sql import and_
from sqlalchemy.orm import Query

from dataall.db import paginate, exceptions
from dataall.modules.omics.db.models import OmicsPipeline
from dataall.core.group.services.group_resource_manager import GroupResource


class OmicsPipelineRepository(GroupResource):
    """DAO layer for Omics"""
    _DEFAULT_PAGE = 1
    _DEFAULT_PAGE_SIZE = 10

    def __init__(self, session):
        self._session = session

    def save_omics_pipeline(self, omics_pipeline):
        """Save Omics Pipeline to the database"""
        self._session.add(omics_pipeline)
        self._session.commit()

# Part of service
    # @staticmethod
    # @has_tenant_perm(permissions.MANAGE_OMICS_PIPELINES)
    # @has_resource_perm(permissions.CREATE_OMICS_PIPELINE)
    # def create_pipeline(
    #     session,
    #     username: str,
    #     groups: [str],
    #     uri: str,
    #     data: dict = None,
    #     check_perm: bool = False,
    # ) -> OmicsPipeline:
    #
    #     OmicsPipeline._validate_input(data)
    #
    #     OmicsPipeline.validate_group_membership(
    #         session=session,
    #         username=username,
    #         groups=groups,
    #         group=data["SamlGroupName"],
    #         environment_uri=uri,
    #     )
    #
    #     environment = Environment.get_environment_by_uri(session, uri)
    #
    #     pipeline: OmicsPipeline = OmicsPipeline(
    #         owner=username,
    #         organizationUri=environment.organizationUri,
    #         environmentUri=environment.environmentUri,
    #         SamlGroupName=data["SamlGroupName"],
    #         label=data["label"],
    #         description=data.get("description", ""),
    #         tags=data.get("tags", []),
    #         AwsAccountId=environment.AwsAccountId,
    #         region=environment.region,
    #         S3InputBucket=data["S3InputBucket"],
    #         S3InputPrefix=data["S3InputPrefix"],
    #         S3OutputBucket=data["S3OutputBucket"],
    #         S3OutputPrefix=data["S3OutputPrefix"],
    #     )
    #     session.add(pipeline)
    #     session.commit()
    #
    #     aws_resources_name = f"{environment.resourcePrefix}-omics-{pipeline.OmicsPipelineUri}"[:63]
    #
    #     pipeline.CodeRepository = aws_resources_name
    #     pipeline.StepFunction = aws_resources_name
    #     pipeline.CiPipeline = aws_resources_name
    #     pipeline.OmicsWorkflow = aws_resources_name
    #
    #     activity = models.Activity(
    #         action="OMICS_PIPELINE:CREATE",
    #         label="OMICS_PIPELINE:CREATE",
    #         owner=username,
    #         summary=f"{username} created OMICS_PIPELINE {pipeline.label} in {environment.label}",
    #         targetUri=pipeline.OmicsPipelineUri,
    #         targetType="OMICS_PIPELINE",
    #     )
    #     session.add(activity)
    #
    #     ResourcePolicy.attach_resource_policy(
    #         session=session,
    #         group=data["SamlGroupName"],
    #         permissions=permissions.OMICS_PIPELINE_ALL,
    #         resource_uri=pipeline.OmicsPipelineUri,
    #         resource_type=OmicsPipeline.__name__,
    #     )
    #
    #     if environment.SamlGroupName != pipeline.SamlGroupName:
    #         ResourcePolicy.attach_resource_policy(
    #             session=session,
    #             group=environment.SamlGroupName,
    #             permissions=permissions.OMICS_PIPELINE_ALL,
    #             resource_uri=pipeline.OmicsPipelineUri,
    #             resource_type=OmicsPipeline.__name__,
    #         )
    #
    #     return pipeline
    #
    # @staticmethod
    # def _validate_input(data):
    #     if not data:
    #         raise exceptions.RequiredParameter(data)
    #     if not data.get("environmentUri"):
    #         raise exceptions.RequiredParameter("environmentUri")
    #     if not data.get("SamlGroupName"):
    #         raise exceptions.RequiredParameter("group")
    #     if not data.get("label"):
    #         raise exceptions.RequiredParameter("label")
    #     if not data.get("S3InputBucket"):
    #         raise exceptions.RequiredParameter("S3InputBucket")
    #     if not data.get("S3OutputBucket"):
    #         raise exceptions.RequiredParameter("S3OutputBucket")
    #     if not data.get("S3InputPrefix"):
    #         raise exceptions.RequiredParameter("S3InputPrefix")
    #     if not data.get("S3OutputPrefix"):
    #         raise exceptions.RequiredParameter("S3OutputPrefix")
    #
    # @staticmethod
    # def validate_group_membership(session, environment_uri, group, username, groups):
    #     if group and group not in groups:
    #         raise exceptions.UnauthorizedOperation(
    #             action=permissions.CREATE_OMICS_PIPELINE,
    #             message=f"User: {username} is not a member of the team {group}",
    #         )
    #     if group not in Environment.list_environment_groups(
    #         session=session,
    #         username=username,
    #         groups=groups,
    #         uri=environment_uri,
    #         data=None,
    #         check_perm=True,
    #     ):
    #         raise exceptions.UnauthorizedOperation(
    #             action=permissions.CREATE_OMICS_PIPELINE,
    #             message=f"Team: {group} is not a member of the environment {environment_uri}",
    #         )
    #
    # @staticmethod
    # def _validate_datasets(environment, input_dataset, output_dataset):
    #     if not input_dataset:
    #         raise exceptions.ObjectNotFound(type="Dataset", id=input_dataset.datasetUri)
    #     if not output_dataset:
    #         raise exceptions.ObjectNotFound(type="Dataset", id=output_dataset.datasetUri)
    #     if not input_dataset.environmentUri != environment.environmentUri:
    #         raise exceptions.EnvironmentResourcesFound(
    #             action=permissions.CREATE_OMICS_PIPELINE,
    #             message=f"Dataset: {input_dataset.datasetUri} is not part of the environment {environment.environmentUri}.",
    #         )
    #     if not output_dataset.environmentUri != environment.environmentUri:
    #         raise exceptions.EnvironmentResourcesFound(
    #             action=permissions.CREATE_OMICS_PIPELINE,
    #             message=f"Dataset: {output_dataset.datasetUri} is not part of the environment {environment.environmentUri}.",
    #         )
    #

    def find_omics_pipeline(self,uri: str):
        """Finds an omics pipeline. Returns None if it doesn't exist"""
        return self._session.query(OmicsPipeline).get(uri)

    # @staticmethod
    # @has_tenant_perm(permissions.MANAGE_OMICS_PIPELINES)
    # @has_resource_perm(permissions.GET_OMICS_PIPELINE)
    # def get_instance(
    #     session,
    #     username: str,
    #     groups: [str],
    #     uri: str,
    #     data: dict = None,
    #     check_perm: bool = False,
    # ) -> OmicsPipeline:
    #     return OmicsPipeline.get_pipeline_by_uri(session, uri)
    #

#Part of service
    # @staticmethod
    # @has_tenant_perm(permissions.MANAGE_OMICS_PIPELINES)
    # @has_resource_perm(permissions.UPDATE_OMICS_PIPELINE)
    # def update_pipeline(session, username, groups, uri, data=None, check_perm=None) -> OmicsPipeline:
    #     pipeline: OmicsPipeline = OmicsPipeline.get_pipeline_by_uri(session, uri)
    #     if data:
    #         if isinstance(data, dict):
    #             for k in data.keys():
    #                 setattr(pipeline, k, data.get(k))
    #     return pipeline


    #@staticmethod
    # def get_pipeline_by_uri(session, uri):
    #     pipeline: OmicsPipeline = session.query(OmicsPipeline).get(uri)
    #     if not pipeline:
    #         raise exceptions.ObjectNotFound("OmicsPipeline", uri)
    #     return pipeline

    def _query_user_pipelines(self, username, groups, filter) -> Query:
        query = self._session.query(OmicsPipeline).filter(
            or_(
                OmicsPipeline.owner == username,
                OmicsPipeline.SamlGroupName.in_(groups),
            )
        )
        if filter and filter.get("term"):
            query = query.filter(
                or_(
                    OmicsPipeline.description.ilike(filter.get("term") + "%%"),
                    OmicsPipeline.label.ilike(filter.get("term") + "%%"),
                )
            )
        return query


    #@staticmethod
    # def query_user_pipelines(session, username, groups, filter) -> Query:
    #     query = session.query(OmicsPipeline).filter(
    #         or_(
    #             OmicsPipeline.owner == username,
    #             OmicsPipeline.SamlGroupName.in_(groups),
    #         )
    #     )
    #     if filter and filter.get("term"):
    #         query = query.filter(
    #             or_(
    #                 OmicsPipeline.description.ilike(filter.get("term") + "%%"),
    #                 OmicsPipeline.label.ilike(filter.get("term") + "%%"),
    #             )
    #         )
    #     return query

    def paginated_user_pipelines(self, username, groups, filter=None) -> dict:
        return paginate(
            query=OmicsPipeline._query_user_pipelines(username, groups, filter),
            page=filter.get('page', OmicsPipelineRepository._DEFAULT_PAGE),
            page_size=filter.get('pageSize', OmicsPipelineRepository._DEFAULT_PAGE_SIZE),
        ).to_dict()

    #@staticmethod
    # def paginated_user_pipelines(session, username, groups, uri, data=None, check_perm=None) -> dict:
    #     return paginate(
    #         query=OmicsPipeline.query_user_pipelines(session, username, groups, data),
    #         page=data.get("page", 1),
    #         page_size=data.get("pageSize", 10),
    #     ).to_dict()

# Part of service
    # @staticmethod
    # @has_tenant_perm(permissions.MANAGE_OMICS_PIPELINES)
    # @has_resource_perm(permissions.DELETE_OMICS_PIPELINE)
    # def delete(session, username, groups, uri, data=None, check_perm=None) -> bool:
    #     pipeline = data.get("pipeline", OmicsPipeline.get_pipeline_by_uri(session, uri))
    #     session.delete(pipeline)
    #     ResourcePolicy.delete_resource_policy(session=session, resource_uri=uri, group=pipeline.SamlGroupName)
    #     session.commit()
    #     return True

    def count_resources(self, environment, group_uri):
        return (
            self._session.query(OmicsPipeline)
            .filter(
                and_(
                    OmicsPipeline.environmentUri == environment.environmentUri,
                    OmicsPipeline.SamlAdminGroupName == group_uri
                )
            )
            .count()
        )