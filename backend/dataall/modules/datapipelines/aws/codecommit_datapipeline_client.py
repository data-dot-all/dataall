from dataall.base.aws.sts import SessionHelper


class DatapipelineCodecommitClient:
    def __init__(self, aws_account_id, region) -> None:
        self._session = SessionHelper.remote_session(aws_account_id)
        self._client = self._session.client('codecommit', region_name=region)

    def get_file_content(self, repository, commit_specifier, file_path):
        response = self._client.get_file(
            repositoryName=repository,
            commitSpecifier=commit_specifier,
            filePath=file_path,
        )
        return response['fileContent']

    def get_folder_content(self, repository, commit_specifier, folder_path):
        response = self._client.get_folder(
            repositoryName=repository,
            commitSpecifier=commit_specifier,
            folderPath=folder_path,
        )
        nodes = []
        for sub_folder in response['subFolders']:
            get_folder_response = self._client.get_folder(
                repositoryName=repository,
                commitSpecifier=commit_specifier,
                folderPath=sub_folder['absolutePath'],
            )
            get_commit = self._client.get_commit(
                repositoryName=repository, commitId=get_folder_response['commitId']
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
            get_file_response = self._client.get_file(
                repositoryName=repository,
                commitSpecifier=commit_specifier,
                filePath=file['absolutePath'],
            )
            get_commit = self._client.get_commit(
                repositoryName=repository, commitId=get_file_response['commitId']
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

    def list_branches(self, repository):
        response = self._client.list_branches(repositoryName=repository)
        return response['branches']

    def delete_repository(self, repository):
        _ = self._client.delete_repository(repositoryName=repository)
        return True
