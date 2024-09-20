import logging
import os

import boto3

from dataall.base.aws.parameter_store import ParameterStoreManager

log = logging.getLogger(__name__)


class IAMClient:
    def __init__(self, session, region):
        if session is None:
            session = boto3.Session()
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

    @staticmethod
    def get_tooling_account_id():
        session = boto3.Session()
        param_client = session.client('ssm', os.environ.get('AWS_REGION', 'us-east-1'))
        parameter_path=f"/dataall/{os.environ.get('ENVNAME', 'dev')}/toolingAccount"
        print(parameter_path)
        toolingAccount = param_client.get_parameter(Name=parameter_path)['Parameter']['Value']
        return toolingAccount

    def create_role(self, account_id, role_name, test_role_name):
        try:
            role = self._client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=f"""{{
                                         "Version": "2012-10-17",
            "Statement": [
                {{
                    "Effect": "Allow",
                    "Principal": {{
                        "AWS": ["arn:aws:iam::{account_id}:root",
                        "arn:aws:iam::{IAMClient.get_tooling_account_id()}:root",
                        "arn:aws:sts::{account_id}:assumed-role/{test_role_name}/{test_role_name}"]
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

    def create_role_if_not_exists(self, account_id, role_name, test_role_name):
        role = self.get_role(role_name)
        if role is None:
            role = self.create_role(account_id, role_name,test_role_name)
        return role

    def get_consumption_role(self, account_id, role_name,test_role_name):
        role = self.get_role(role_name)
        if role is None:
            role = self.create_role(account_id, role_name,test_role_name)
            self.put_consumption_role_policy(role_name)
        return role

    def put_consumption_role_policy(self, role_name):
        self._client.put_role_policy(
            RoleName=role_name,
            PolicyName='ConsumptionPolicy',
            PolicyDocument="""{
                                        "Version": "2012-10-17",
                                        "Statement": [
                                            {
                                                "Sid": "VisualEditor0",
                                                "Effect": "Allow",
                                                "Action": [
                                                    "s3:*",
                                                    "athena:*",
                                                    "glue:*",
                                                    "lakeformation:GetDataAccess"
                                                ],
                                                "Resource": "*"
                                            }
                                        ]
                                    }""",
        )
