from sqlalchemy import or_, and_
from sqlalchemy.orm import Query

from dataall.core.environment.db.environment_models import Environment
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.environment.services.environment_resource_manager import EnvironmentResource
from dataall.core.stacks.db.stack_models import Stack
from dataall.core.activity.db.activity_models import Activity
from dataall.base.db import exceptions, paginate
from dataall.modules.datapipelines.db.datapipelines_models import DataPipeline, DataPipelineEnvironment
from dataall.base.utils.naming_convention import (
    NamingConventionService,
    NamingConventionPattern,
)
from dataall.base.utils import slugify


class DatapipelinesRepository(EnvironmentResource):
    """DAO layer for datapipelines"""

    _DEFAULT_PAGE = 1
    _DEFAULT_PAGE_SIZE = 10

    def count_resources(self, session, environment, group_uri) -> int:
        return (
            session.query(DataPipeline)
            .filter(
                and_(DataPipeline.environmentUri == environment.environmentUri, DataPipeline.SamlGroupName == group_uri)
            )
            .count()
        )

    @staticmethod
    def create_pipeline(
        session,
        username: str,
        admin_group: str,
        uri: str,
        data: dict = None,
    ) -> DataPipeline:
        environment = EnvironmentService.get_environment_by_uri(session, uri)

        pipeline: DataPipeline = DataPipeline(
            owner=username,
            environmentUri=environment.environmentUri,
            SamlGroupName=admin_group,
            label=data['label'],
            description=data.get('description', 'No description provided'),
            tags=data.get('tags', []),
            AwsAccountId=environment.AwsAccountId,
            region=environment.region,
            repo=slugify(data['label']),
            devStrategy=data['devStrategy'],
            template='',
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

        activity = Activity(
            action='PIPELINE:CREATE',
            label='PIPELINE:CREATE',
            owner=username,
            summary=f'{username} created pipeline {pipeline.label} in {environment.label}',
            targetUri=pipeline.DataPipelineUri,
            targetType='pipeline',
        )
        session.add(activity)
        return pipeline

    @staticmethod
    def get_pipeline_by_uri(session, uri):
        pipeline: DataPipeline = session.query(DataPipeline).get(uri)
        if not pipeline:
            raise exceptions.ObjectNotFound('DataPipeline', uri)
        return pipeline

    @staticmethod
    def get_pipeline_environment_by_uri(session, uri):
        pipeline_env: DataPipelineEnvironment = session.query(DataPipelineEnvironment).get(uri)
        if not pipeline_env:
            raise exceptions.ObjectNotFound('PipelineEnvironment', uri)
        return pipeline_env

    @staticmethod
    def get_pipeline_and_environment_by_uri(session, uri):
        pipeline: DataPipeline = session.query(DataPipeline).get(uri)
        env: Environment = session.query(Environment).get(pipeline.environmentUri)
        return (pipeline, env)

    @staticmethod
    def get_pipeline_stack_by_uri(session, uri):
        return (
            session.query(Stack)
            .filter(
                and_(
                    Stack.targetUri == uri,
                    Stack.stack == 'PipelineStack',
                )
            )
            .first()
        )

    @staticmethod
    def query_user_pipelines(session, username, groups, filter) -> Query:
        query = session.query(DataPipeline).filter(
            or_(
                DataPipeline.owner == username,
                DataPipeline.SamlGroupName.in_(groups),
            )
        )
        if filter and filter.get('term'):
            query = query.filter(
                or_(
                    DataPipeline.description.ilike(filter.get('term') + '%%'),
                    DataPipeline.label.ilike(filter.get('term') + '%%'),
                )
            )
        if filter and filter.get('region'):
            if len(filter.get('region')) > 0:
                query = query.filter(DataPipeline.region.in_(filter.get('region')))
        if filter and filter.get('tags'):
            if len(filter.get('tags')) > 0:
                query = query.filter(or_(*[DataPipeline.tags.any(tag) for tag in filter.get('tags')]))
        if filter and filter.get('type'):
            if len(filter.get('type')) > 0:
                query = query.filter(DataPipeline.devStrategy.in_(filter.get('type')))
        return query.order_by(DataPipeline.label)

    @staticmethod
    def paginated_user_pipelines(session, username, groups, data=None) -> dict:
        return paginate(
            query=DatapipelinesRepository.query_user_pipelines(session, username, groups, data),
            page=data.get('page', DatapipelinesRepository._DEFAULT_PAGE),
            page_size=data.get('pageSize', DatapipelinesRepository._DEFAULT_PAGE_SIZE),
        ).to_dict()

    @staticmethod
    def query_pipeline_environments(session, uri) -> Query:
        query = session.query(DataPipelineEnvironment).filter(
            DataPipelineEnvironment.pipelineUri.ilike(uri + '%%'),
        )
        return query.order_by(DataPipelineEnvironment.stage)

    @staticmethod
    def paginated_pipeline_environments(session, uri, data=None) -> dict:
        return paginate(
            query=DatapipelinesRepository.query_pipeline_environments(session, uri),
            page=data.get('page', DatapipelinesRepository._DEFAULT_PAGE),
            page_size=data.get('pageSize', DatapipelinesRepository._DEFAULT_PAGE_SIZE),
        ).to_dict()

    @staticmethod
    def delete_pipeline_environments(session, uri) -> bool:
        deletedItems = (
            session.query(DataPipelineEnvironment).filter(DataPipelineEnvironment.pipelineUri == uri).delete()
        )
        session.commit()
        return True

    @staticmethod
    def delete_pipeline_environment(session, envPipelineUri) -> bool:
        deletedItem = (
            session.query(DataPipelineEnvironment)
            .filter(DataPipelineEnvironment.envPipelineUri == envPipelineUri)
            .delete()
        )
        session.commit()
        return True

    @staticmethod
    def get_pipeline_environment(session, pipelineUri, environmentUri, stage) -> DataPipelineEnvironment:
        return (
            session.query(DataPipelineEnvironment)
            .filter(
                and_(
                    DataPipelineEnvironment.pipelineUri == pipelineUri,
                    DataPipelineEnvironment.environmentUri == environmentUri,
                    DataPipelineEnvironment.stage == stage,
                )
            )
            .first()
        )
