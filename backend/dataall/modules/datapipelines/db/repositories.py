from sqlalchemy import or_, and_
from sqlalchemy.orm import Query

from dataall.core.group.services.group_resource_manager import GroupResource
from dataall.db import models, exceptions, paginate
from dataall.modules.datapipelines.db.models import DataPipeline, DataPipelineEnvironment


class DatapipelinesRepository(GroupResource):
    """DAO layer for datapipelines"""
    _DEFAULT_PAGE = 1
    _DEFAULT_PAGE_SIZE = 10
    
    @staticmethod
    def get_clone_url_http(session, environmentUri, repo):
        env: models.Environment = session.query(models.Environment).get(
            environmentUri
        )
        return f'codecommit::{env.region}://{repo}'
    
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
        env: models.Environment = session.query(models.Environment).get(pipeline.environmentUri)
        return (pipeline, env)
    
    @staticmethod
    def get_pipeline_stack_by_uri(session, uri):
        return (session.query(models.Stack)
            .filter(
                and_(
                    models.Stack.targetUri == uri,
                    models.Stack.stack == 'PipelineStack',
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
                query = query.filter(
                    DataPipeline.region.in_(filter.get('region'))
                )
        if filter and filter.get('tags'):
            if len(filter.get('tags')) > 0:
                query = query.filter(
                    or_(
                        *[DataPipeline.tags.any(tag) for tag in filter.get('tags')]
                    )
                )
        if filter and filter.get('type'):
            if len(filter.get('type')) > 0:
                query = query.filter(
                    DataPipeline.devStrategy.in_(filter.get('type'))
                )
        return query

    @staticmethod
    def paginated_user_pipelines(
        session, username, groups, data=None
    ) -> dict:
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
        return query
    
    @staticmethod
    def paginated_pipeline_environments(
        session, uri, data=None
    ) -> dict:
        return paginate(
            query=DatapipelinesRepository.query_pipeline_environments(session, uri),
            page=data.get('page', DatapipelinesRepository._DEFAULT_PAGE),
            page_size=data.get('pageSize', DatapipelinesRepository._DEFAULT_PAGE_SIZE),
        ).to_dict()

    @staticmethod
    def delete_pipeline_environments(session, uri) -> bool:
        deletedItems = (
            session.query(DataPipelineEnvironment).filter(
                DataPipelineEnvironment.pipelineUri == uri).delete()
        )
        session.commit()
        return True
    
    @staticmethod
    def delete_pipeline_environment(
        session, envPipelineUri
    ) -> bool:
        deletedItem = (
            session.query(DataPipelineEnvironment).filter(
                DataPipelineEnvironment.envPipelineUri == envPipelineUri).delete()
        )
        session.commit()
        return True
    
    @staticmethod
    def get_pipeline_environment(
        session, pipelineUri, environmentUri, stage
        ) -> DataPipelineEnvironment:
        return session.query(DataPipelineEnvironment).filter(
            and_(
                DataPipelineEnvironment.pipelineUri == pipelineUri,
                DataPipelineEnvironment.environmentUri == environmentUri,
                DataPipelineEnvironment.stage == stage
            )
        ).first()
