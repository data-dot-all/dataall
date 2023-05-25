import logging

from sqlalchemy import or_, and_
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
            devStrategy=data['devStrategy'],
            template="",
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
    def create_pipeline_environment(
        session,
        username: str,
        groups: [str],
        data: dict = None,
        check_perm: bool = False,
    ) -> models.DataPipelineEnvironment:

        Environment.check_group_environment_permission(
            session=session,
            username=username,
            groups=groups,
            uri=data['environmentUri'],
            group=data['samlGroupName'],
            permission_name=permissions.CREATE_PIPELINE,
        )

        environment = Environment.get_environment_by_uri(session, data['environmentUri'])

        if not environment.pipelinesEnabled:
            raise exceptions.UnauthorizedOperation(
                action=permissions.CREATE_PIPELINE,
                message=f'Pipelines feature is disabled for the environment {environment.label}',
            )

        pipeline = Pipeline.get_pipeline_by_uri(session, data['pipelineUri'])

        pipeline_env: models.DataPipelineEnvironment = models.DataPipelineEnvironment(
            owner=username,
            label=f"{pipeline.label}-{environment.label}",
            environmentUri=environment.environmentUri,
            environmentLabel=environment.label,
            pipelineUri=pipeline.DataPipelineUri,
            pipelineLabel=pipeline.label,
            envPipelineUri=f"{pipeline.DataPipelineUri}{environment.environmentUri}{data['stage']}",
            AwsAccountId=environment.AwsAccountId,
            region=environment.region,
            stage=data['stage'],
            order=data['order'],
            samlGroupName=data['samlGroupName']
        )

        session.add(pipeline_env)
        session.commit()

        return pipeline_env

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
        if filter and filter.get('region'):
            if len(filter.get('region')) > 0:
                query = query.filter(
                    models.DataPipeline.region.in_(filter.get('region'))
                )
        if filter and filter.get('tags'):
            if len(filter.get('tags')) > 0:
                query = query.filter(
                    or_(
                        *[models.DataPipeline.tags.any(tag) for tag in filter.get('tags')]
                    )
                )
        if filter and filter.get('type'):
            if len(filter.get('type')) > 0:
                query = query.filter(
                    models.DataPipeline.devStrategy.in_(filter.get('type'))
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

    @staticmethod
    @has_tenant_perm(permissions.MANAGE_PIPELINES)
    @has_resource_perm(permissions.GET_PIPELINE)
    def get_pipeline_environment(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ) -> models.DataPipeline:
        return Pipeline.get_pipeline_environment_by_uri(session, uri)

    @staticmethod
    def get_pipeline_environment_by_uri(session, uri):
        pipeline_env: models.DataPipelineEnvironment = session.query(models.DataPipelineEnvironment).get(uri)
        if not pipeline_env:
            raise exceptions.ObjectNotFound('PipelineEnvironment', uri)
        return pipeline_env

    @staticmethod
    def query_pipeline_environments(session, uri) -> Query:
        query = session.query(models.DataPipelineEnvironment).filter(
            models.DataPipelineEnvironment.pipelineUri.ilike(uri + '%%'),
        )
        return query

    @staticmethod
    def delete_pipeline_environments(session, uri) -> bool:
        deletedItems = (
            session.query(models.DataPipelineEnvironment).filter(
                models.DataPipelineEnvironment.pipelineUri == uri).delete()
        )
        session.commit()
        return True

    @staticmethod
    def delete_pipeline_environment(
        session, username, groups, envPipelineUri, check_perm=None
    ) -> bool:
        deletedItem = (
            session.query(models.DataPipelineEnvironment).filter(
                models.DataPipelineEnvironment.envPipelineUri == envPipelineUri).delete()
        )
        session.commit()
        return True

    @staticmethod
    @has_tenant_perm(permissions.MANAGE_PIPELINES)
    @has_resource_perm(permissions.UPDATE_PIPELINE)
    def update_pipeline_environment(
        session, username, groups, uri, data=None, check_perm=None
    ) -> models.DataPipelineEnvironment:
        pipeline_env = session.query(models.DataPipelineEnvironment).filter(
            and_(
                models.DataPipelineEnvironment.pipelineUri == data['pipelineUri'],
                models.DataPipelineEnvironment.environmentUri == data['environmentUri'],
                models.DataPipelineEnvironment.stage == data['stage']
            )
        ).first()
        if data:
            if isinstance(data, dict):
                for k in data.keys():
                    print(f"KEY: {k}, VALUE: {data.get(k)}")
                    setattr(pipeline_env, k, data.get(k))
        return pipeline_env

    @staticmethod
    def paginated_pipeline_environments(
        session, username, groups, uri, data=None, check_perm=None
    ) -> dict:
        return paginate(
            query=Pipeline.query_pipeline_environments(session, uri),
            page=data.get('page', 1),
            page_size=data.get('pageSize', 10),
        ).to_dict()
