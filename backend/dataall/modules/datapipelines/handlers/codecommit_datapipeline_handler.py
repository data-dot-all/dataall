from dataall.aws.handlers.service_handlers import Worker
from dataall.db import models, Engine
from dataall.modules.datapipelines.aws.codecommit_datapipeline_client import DatapipelineCodecommitClient
from dataall.modules.datapipelines.db.repositories import DatapipelinesRepository


class DatapipelineCodeCommitHandler:
    def __init__(self):
        pass

    @staticmethod
    def _unpack(session, task):
        return DatapipelinesRepository.get_pipeline_and_environment_by_uri(
            session=session,
            uri=task.targetUri
        )

    @staticmethod
    @Worker.handler(path='repo.datapipeline.cat')
    def cat(engine: Engine, task: models.Task):
        with engine.scoped_session() as session:
            (pipeline, env) = DatapipelineCodeCommitHandler._unpack(session, task)

            return DatapipelineCodecommitClient(env.AwsAccountId, env.region).get_file_content(
                repository=pipeline.repo,
                commit_specifier=task.payload.get('branch', 'master'),
                file_path=task.payload.get('absolutePath', 'README.md')
            )

    @staticmethod
    @Worker.handler(path='repo.datapipeline.ls')
    def ls(engine: Engine, task: models.Task):
        with engine.scoped_session() as session:
            (pipeline, env) = DatapipelineCodeCommitHandler._unpack(session, task)

            return DatapipelineCodecommitClient(env.AwsAccountId, env.region).get_folder_content(
                repository=pipeline.repo,
                commit_specifier=task.payload.get('branch', 'master'),
                folder_path=task.payload.get('folderPath')
            )

    @staticmethod
    @Worker.handler(path='repo.datapipeline.branches')
    def list_branches(engine: Engine, task: models.Task):
        with engine.scoped_session() as session:
            (pipeline, env) = DatapipelineCodeCommitHandler._unpack(session, task)

            return DatapipelineCodecommitClient(env.AwsAccountId, env.region).list_branches(
                repository=pipeline.repo
            )

    @staticmethod
    @Worker.handler(path='repo.datapipeline.delete')
    def delete_repository(engine: Engine, task: models.Task):
        with engine.scoped_session() as session:
            aws_account_id = task.payload.get('accountid', '111111111111')
            region = task.payload.get('region', 'eu-west-1')
            return DatapipelineCodecommitClient(aws_account_id, region).delete_repository(
                repository=task.payload.get("repo_name", "dataall-repo")
            )

