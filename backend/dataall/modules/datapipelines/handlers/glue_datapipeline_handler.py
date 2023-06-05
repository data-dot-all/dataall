import logging

from dataall.aws.handlers.service_handlers import Worker
from dataall.db import models
from dataall.modules.datapipelines.db.models import DataPipeline
from dataall.modules.datapipelines.db.repositories import DatapipelinesRepository
from dataall.modules.datapipelines.aws.glue_datapipeline_client import GlueDatapipelineClient

log = logging.getLogger('aws:glue')


@Worker.handler(path='glue.job.runs')
def get_job_runs(engine, task: models.Task):
    with engine.scoped_session() as session:
        data_pipeline: DataPipeline = DatapipelinesRepository.get_pipeline_by_uri(task.targetUri)
        
        return GlueDatapipelineClient(
            aws_account_id=data_pipeline.AwsAccountId,
            region=data_pipeline.region
        ).get_job_runs(datapipeline_job_name=data_pipeline.name)
