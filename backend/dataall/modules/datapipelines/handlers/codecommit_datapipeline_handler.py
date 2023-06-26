from dataall.aws.handlers.service_handlers import Worker
from dataall.db import models, Engine
from dataall.modules.datapipelines.aws.codecommit_datapipeline_client import DatapipelineCodecommitClient


class DatapipelineCodeCommitHandler:
    def __init__(self):
        pass

    @staticmethod
    @Worker.handler(path='repo.datapipeline.delete')
    def delete_repository(engine: Engine, task: models.Task):
        with engine.scoped_session() as session:
            aws_account_id = task.payload.get('accountid', '111111111111')
            region = task.payload.get('region', 'eu-west-1')
            return DatapipelineCodecommitClient(aws_account_id, region).delete_repository(
                repository=task.payload.get("repo_name", "dataall-repo")
            )
