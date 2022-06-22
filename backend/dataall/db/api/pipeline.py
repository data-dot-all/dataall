import logging

from sqlalchemy import or_
from sqlalchemy.orm import Query

from . import (
    Environment,
    has_tenant_perm,
    has_resource_perm,
    ResourcePolicy,
)
from .. import models, exceptions, permissions
from .. import paginate
from ...utils.naming_convention import (
    NamingConventionService,
    NamingConventionPattern,
)
from ...utils.slugify import slugify

logger = logging.getLogger(__name__)


class Pipeline:
    @staticmethod
    @has_tenant_perm(permissions.MANAGE_PIPELINES)
    @has_resource_perm(permissions.CREATE_PIPELINE)
    def create_pipeline(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ) -> models.DataPipeline:

        Pipeline._validate_input(data)

        Environment.check_group_environment_permission(
            session=session,
            username=username,
            groups=groups,
            uri=uri,
            group=data['SamlGroupName'],
            permission_name=permissions.CREATE_PIPELINE,
        )

        environment = Environment.get_environment_by_uri(session, uri)

        if not environment.pipelinesEnabled:
            raise exceptions.UnauthorizedOperation(
                action=permissions.CREATE_PIPELINE,
                message=f'Pipelines feature is disabled for the environment {environment.label}',
            )

        pipeline: models.DataPipeline = models.DataPipeline(
            owner=username,
            environmentUri=environment.environmentUri,
            SamlGroupName=data['SamlGroupName'],
            label=data['label'],
            description=data.get('description', 'No description provided'),
            tags=data.get('tags', []),
            AwsAccountId=environment.AwsAccountId,
            region=environment.region,
            repo=slugify(data['label']),
            devStages=data.get('devStages', []),
            devStrategy=data['devStrategy'],
            inputDatasetUri=data['inputDatasetUri'],
            outputDatasetUri=data['outputDatasetUri'],
            template=data['template'],
        )

        session.add(pipeline)
        session.commit()

        aws_compliant_name = NamingConventionService(
            target_uri=pipeline.DataPipelineUri,
            target_label=pipeline.label,
            pattern=NamingConventionPattern.DEFAULT,
            resource_prefix=environment.resourcePrefix,
        ).build_compliant_name()

        pipeline.repo = aws_compliant_name
        pipeline.name = aws_compliant_name

        activity = models.Activity(
            action='PIPELINE:CREATE',
            label='PIPELINE:CREATE',
            owner=username,
            summary=f'{username} created dashboard {pipeline.label} in {environment.label}',
            targetUri=pipeline.DataPipelineUri,
            targetType='pipeline',
        )
        session.add(activity)

        ResourcePolicy.attach_resource_policy(
            session=session,
            group=data['SamlGroupName'],
            permissions=permissions.PIPELINE_ALL,
            resource_uri=pipeline.DataPipelineUri,
            resource_type=models.DataPipeline.__name__,
        )

        if environment.SamlGroupName != pipeline.SamlGroupName:
            ResourcePolicy.attach_resource_policy(
                session=session,
                group=environment.SamlGroupName,
                permissions=permissions.PIPELINE_ALL,
                resource_uri=pipeline.DataPipelineUri,
                resource_type=models.DataPipeline.__name__,
            )

        return pipeline

    @staticmethod
    def _validate_input(data):
        if not data:
            raise exceptions.RequiredParameter(data)
        if not data.get('environmentUri'):
            raise exceptions.RequiredParameter('environmentUri')
        if not data.get('SamlGroupName'):
            raise exceptions.RequiredParameter('group')
        if not data.get('label'):
            raise exceptions.RequiredParameter('label')

    @staticmethod
    def validate_group_membership(
        session, environment_uri, pipeline_group, username, groups
    ):
        if pipeline_group and pipeline_group not in groups:
            raise exceptions.UnauthorizedOperation(
                action=permissions.CREATE_PIPELINE,
                message=f'User: {username} is not a member of the team {pipeline_group}',
            )
        if pipeline_group not in Environment.list_environment_groups(
            session=session,
            username=username,
            groups=groups,
            uri=environment_uri,
            data=None,
            check_perm=True,
        ):
            raise exceptions.UnauthorizedOperation(
                action=permissions.CREATE_PIPELINE,
                message=f'Team: {pipeline_group} is not a member of the environment {environment_uri}',
            )

    @staticmethod
    @has_tenant_perm(permissions.MANAGE_PIPELINES)
    @has_resource_perm(permissions.GET_PIPELINE)
    def get_pipeline(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ) -> models.DataPipeline:
        return Pipeline.get_pipeline_by_uri(session, uri)

    @staticmethod
    @has_tenant_perm(permissions.MANAGE_PIPELINES)
    @has_resource_perm(permissions.UPDATE_PIPELINE)
    def update_pipeline(
        session, username, groups, uri, data=None, check_perm=None
    ) -> models.DataPipeline:
        pipeline: models.DataPipeline = Pipeline.get_pipeline_by_uri(session, uri)
        if data:
            if isinstance(data, dict):
                for k in data.keys():
                    setattr(pipeline, k, data.get(k))
        return pipeline

    @staticmethod
    def get_pipeline_by_uri(session, uri):
        pipeline: models.DataPipeline = session.query(models.DataPipeline).get(uri)
        if not pipeline:
            raise exceptions.ObjectNotFound('Pipeline', uri)
        return pipeline

    @staticmethod
    def query_user_pipelines(session, username, groups, filter) -> Query:
        query = session.query(models.DataPipeline).filter(
            or_(
                models.DataPipeline.owner == username,
                models.DataPipeline.SamlGroupName.in_(groups),
            )
        )
        if filter and filter.get('term'):
            query = query.filter(
                or_(
                    models.DataPipeline.description.ilike(filter.get('term') + '%%'),
                    models.DataPipeline.label.ilike(filter.get('term') + '%%'),
                )
            )
        return query

    @staticmethod
    def paginated_user_pipelines(
        session, username, groups, uri, data=None, check_perm=None
    ) -> dict:
        return paginate(
            query=Pipeline.query_user_pipelines(session, username, groups, data),
            page=data.get('page', 1),
            page_size=data.get('pageSize', 10),
        ).to_dict()

    @staticmethod
    def delete(session, username, groups, uri, data=None, check_perm=None) -> bool:
        pipeline = Pipeline.get_pipeline_by_uri(session, uri)
        ResourcePolicy.delete_resource_policy(
            session=session, resource_uri=uri, group=pipeline.SamlGroupName
        )
        session.delete(pipeline)
        session.commit()
        return True
