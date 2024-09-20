import boto3


class StsClient:
    def __init__(self, session, region):
        if not session:
            session = boto3.Session()
        self._client = session.client('sts', region_name=region)
        self._region = region

    def get_role_session(self, role_arn):
        assumed_role_object = self._client.assume_role(RoleArn=role_arn, RoleSessionName='AssumeRole')
        credentials = assumed_role_object['Credentials']

        return boto3.Session(
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken'],
        )
