from dataall.base.aws.sts import SessionHelper


class DatapipelineCodecommitClient:
    def __init__(self, aws_account_id, region) -> None:
        self._session = SessionHelper.remote_session(aws_account_id, region)
        self._client = self._session.client('codecommit', region_name=region)

    def delete_repository(self, repository):
        self._client.delete_repository(repositoryName=repository)
        return True
