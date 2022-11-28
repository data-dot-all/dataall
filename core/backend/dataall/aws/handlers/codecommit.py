from .service_handlers import Worker
from .sts import SessionHelper
from ...db import models, Engine


class CodeCommit:
    def __init__(self):
        pass

    @staticmethod
    def client(AwsAccountId, region):
        session = SessionHelper.remote_session(AwsAccountId)
        return session.client('codecommit', region_name=region)

    @staticmethod
    def _unpack(session, task):
        pipe: models.DataPipeline = session.query(models.DataPipeline).get(task.targetUri)
        env: models.Environment = session.query(models.Environment).get(pipe.environmentUri)
        client = CodeCommit.client(AwsAccountId=env.AwsAccountId, region=env.region)
        return (pipe, env, client)

    @staticmethod
    @Worker.handler(path='repo.datapipeline.cat')
    def cat(engine: Engine, task: models.Task):
        with engine.scoped_session() as session:
            (pipe, env, client) = CodeCommit._unpack(session, task)
            response = client.get_file(
                repositoryName=pipe.repo,
                commitSpecifier=task.payload.get('branch', 'master'),
                filePath=task.payload.get('absolutePath', 'README.md'),
            )
            return response['fileContent']

    @staticmethod
    @Worker.handler(path='repo.datapipeline.ls')
    def ls(engine: Engine, task: models.Task):
        with engine.scoped_session() as session:
            (pipe, env, client) = CodeCommit._unpack(session, task)
            response = client.get_folder(
                repositoryName=pipe.repo,
                commitSpecifier=task.payload.get('branch', 'master'),
                folderPath=task.payload.get('folderPath'),
            )
            nodes = []
            for sub_folder in response['subFolders']:
                get_folder_response = client.get_folder(
                    repositoryName=pipe.repo,
                    commitSpecifier=task.payload.get('branch', 'master'),
                    folderPath=sub_folder['absolutePath'],
                )
                get_commit = client.get_commit(
                    repositoryName=pipe.repo, commitId=get_folder_response['commitId']
                )
                commit = get_commit['commit']
                nodes.append(
                    {
                        'type': 'folder',
                        'author': commit['author'],
                        'relativePath': sub_folder['relativePath'],
                        'absolutePath': sub_folder['absolutePath'],
                    }
                )
            for file in response['files']:
                get_file_response = client.get_file(
                    repositoryName=pipe.repo,
                    commitSpecifier=task.payload.get('branch', 'master'),
                    filePath=file['absolutePath'],
                )
                get_commit = client.get_commit(
                    repositoryName=pipe.repo, commitId=get_file_response['commitId']
                )
                commit = get_commit['commit']
                nodes.append(
                    {
                        'type': 'file',
                        'author': commit['author'],
                        'relativePath': file['relativePath'],
                        'absolutePath': file['absolutePath'],
                    }
                )
            return nodes

    @staticmethod
    @Worker.handler(path='repo.datapipeline.branches')
    def list_branches(engine: Engine, task: models.Task):
        with engine.scoped_session() as session:
            (pipe, env, client) = CodeCommit._unpack(session, task)
            response = client.list_branches(repositoryName=pipe.repo)
            return response['branches']
