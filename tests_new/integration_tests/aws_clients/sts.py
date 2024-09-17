import boto3


class StsClient:
    def __init__(self, session, profile, region):
        if session is None:
            if profile is None:
                session = boto3.Session()
            else:
                session = boto3.Session(profile_name=profile)
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
