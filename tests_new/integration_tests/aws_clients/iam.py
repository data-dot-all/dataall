import logging

import boto3

log = logging.getLogger(__name__)


class IAMClient:
    def __init__(self, session, profile, region):
        if session is None:
            if profile is None:
                session = boto3.Session()
            else:
                session = boto3.Session(profile_name=profile)
        self._client = session.client('iam', region_name=region)
        self._resource = session.resource('iam', region_name=region)
        self._region = region

    def get_role(self, role_name):
        try:
            role = self._client.get_role(RoleName=role_name)
            return role
        except Exception as e:
            log.info(f'Error occurred: {e}')
            return None

    def create_role(self, account_id, role_name):
        try:
            role = self._client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=f"""{{
                                         "Version": "2012-10-17",
            "Statement": [
                {{
                    "Effect": "Allow",
                    "Principal": {{
                        "AWS": "arn:aws:iam::{account_id}:root"
                    }},
                    "Action": "sts:AssumeRole",
                    "Condition": {{}}
                }}
            ]
            }}""",
                Description='Role for Lambda function',
            )
            return role
        except Exception as e:
            log.error(e)
            raise e

    def create_role_if_not_exists(self, account_id, role_name):
        role = self.get_role(role_name)
        if role is None:
            role = self.create_role(account_id, role_name)
        return role
