from uuid import uuid4
import boto3
from boto3 import Session
from botocore.credentials import RefreshableCredentials
from botocore.session import get_session

SESSION_EXPIRATION_TIME_IN_SECONDS = 3600


class STSClient:
    def __init__(self, role_arn, region, session_name=None):
        self.role_arn = role_arn
        self.region = region
        self.session_name = session_name or uuid4().hex

    def _refresh_credentials(self):
        params = {
            'RoleArn': self.role_arn,
            'RoleSessionName': self.session_name,
            'DurationSeconds': SESSION_EXPIRATION_TIME_IN_SECONDS,
        }
        sts_client = boto3.client('sts', region_name=self.region)

        response = sts_client.assume_role(**params).get('Credentials')
        credentials = {
            'access_key': response.get('AccessKeyId'),
            'secret_key': response.get('SecretAccessKey'),
            'token': response.get('SessionToken'),
            'expiry_time': response.get('Expiration').isoformat(),
        }
        return credentials

    def get_refreshable_session(self) -> Session:
        """
        Get refreshable boto3 session.
        """
        refreshable_credentials = RefreshableCredentials.create_from_metadata(
            metadata=self._refresh_credentials(),
            refresh_using=self._refresh_credentials,
            method='sts-assume-role',
        )

        session = get_session()
        session._credentials = refreshable_credentials
        session.set_config_variable('region', self.region)
        return Session(botocore_session=session)

    def get_role_session(self, session) -> Session:
        sts_client = session.client('sts', region_name=self.region)
        assumed_role_object = sts_client.assume_role(RoleArn=self.role_arn, RoleSessionName=self.session_name)
        credentials = assumed_role_object['Credentials']

        return boto3.Session(
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken'],
        )
