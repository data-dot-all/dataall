import logging

from botocore.exceptions import ClientError

from .service_handlers import Worker
from .sts import SessionHelper
from ...db import models

log = logging.getLogger('aws:glue')


class Glue:
    def __init__(self):
        pass

    @staticmethod
    @Worker.handler(path='glue.job.runs')
    def get_job_runs(engine, task: models.Task):
        with engine.scoped_session() as session:
            Data_pipeline: models.DataPipeline = session.query(models.DataPipeline).get(
                task.targetUri
            )
            aws = SessionHelper.remote_session(Data_pipeline.AwsAccountId)
            glue_client = aws.client('glue', region_name=Data_pipeline.region)
            try:
                response = glue_client.get_job_runs(JobName=Data_pipeline.name)
            except ClientError as e:
                log.warning(f'Could not retrieve pipeline runs , {str(e)}')
                return []
            return response['JobRuns']
