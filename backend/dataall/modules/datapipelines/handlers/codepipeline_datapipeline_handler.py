import logging

from dataall.db import models, Engine
from dataall.aws.handlers.service_handlers import Worker
from dataall.modules.datapipelines.aws.codepipeline_datapipeline_client import CodepipelineDatapipelineClient
from dataall.modules.datapipelines.db.models import DataPipeline
from dataall.modules.datapipelines.db.repositories import DatapipelinesRepository

log = logging.getLogger('aws:codepipeline')


@Worker.handler('datapipeline.pipeline.executions')
def get_pipeline_execution(engine: Engine, task: models.Task):
    with engine.scoped_session() as session:
        stack = DatapipelinesRepository.get_pipeline_stack_by_uri(session, task.targetUri)
        datapipeline: DataPipeline = DatapipelinesRepository.get_pipeline_by_uri(session, task.targetUri)
        outputs = stack.outputs
        codepipeline_name = outputs['PipelineNameOutput']
        
        return CodepipelineDatapipelineClient(
            aws_account_id=datapipeline.AwsAccountId,
            region=datapipeline.region
        ).get_pipeline_execution_summaries(codepipeline_name=codepipeline_name)
