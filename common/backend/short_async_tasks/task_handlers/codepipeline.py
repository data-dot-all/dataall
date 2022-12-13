import logging

from botocore.exceptions import ClientError
from sqlalchemy import and_

from ...db import models, Engine
from backend.short_async_tasks import Worker
from .sts import SessionHelper

log = logging.getLogger('aws:codepipeline')


@Worker.handler('datapipeline.pipeline.executions')
def get_pipeline_execution(engine: Engine, task: models.Task):
    with engine.scoped_session() as session:
        stack = (
            session.query(models.Stack)
            .filter(
                and_(
                    models.Stack.targetUri == task.targetUri,
                    models.Stack.stack == 'PipelineStack',
                )
            )
            .first()
        )
        Datapipeline: models.DataPipeline = session.query(models.DataPipeline).get(
            task.targetUri
        )
        outputs = stack.outputs
        codepipeline_name = outputs['PipelineNameOutput']
        aws = SessionHelper.remote_session(Datapipeline.AwsAccountId)
        codepipeline_client = aws.client('codepipeline', region_name=Datapipeline.region)
        executions = []
        try:
            response = codepipeline_client.list_pipeline_executions(
                pipelineName=codepipeline_name
            )
            executions = response['pipelineExecutionSummaries']
        except ClientError as e:
            log.warning(
                f'Could not retrieve pipeline executions for {codepipeline_name} aws://{Datapipeline.AwsAccountId}:{Datapipeline.region}'
            )

        return executions
