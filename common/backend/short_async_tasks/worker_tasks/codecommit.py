from backend.short_async_tasks import Worker
from backend.aws.codecommit import CodeCommit
from backend.db import Engine, common


##TODO: check where it is used - I think it is unused and we could use it for updated in datapipeline edit
@Worker.handler(path='repo.datapipeline.cat')
def cat(engine: Engine, task: common.models.Task):
    with engine.scoped_session() as session:
        (pipe, env, client) = CodeCommit._unpack(session, task)
        response = client.get_file(
            repositoryName=pipe.repo,
            commitSpecifier=task.payload.get('branch', 'master'),
            filePath=task.payload.get('absolutePath', 'README.md'),
        )
        return response['fileContent']


@Worker.handler(path='repo.datapipeline.ls')
def ls(engine: Engine, task: common.models.Task):
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


@Worker.handler(path='repo.datapipeline.branches')
def list_branches(engine: Engine, task: common.models.Task):
    with engine.scoped_session() as session:
        (pipe, env, client) = CodeCommit._unpack(session, task)
        response = client.list_branches(repositoryName=pipe.repo)
        return response['branches']
