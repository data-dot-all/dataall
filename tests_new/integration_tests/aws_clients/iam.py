import json
import logging
import os

import boto3

log = logging.getLogger(__name__)


class IAMClient:
    CONSUMPTION_POLICY_NAME = 'ConsumptionPolicy'

    def __init__(self, session=boto3.Session(), region=os.environ.get('AWS_REGION', 'us-east-1')):
        self._client = session.client('iam', region_name=region)
        self._resource = session.resource('iam', region_name=region)
        self._region = region

    def get_role(self, role_name):
        try:
            role = self._client.get_role(RoleName=role_name)
            return role
        except self._client.exceptions.NoSuchEntityException as e:
            log.info(f'Error occurred: {e}')
            return None

    def delete_role(self, role_name):
        self._client.delete_role(RoleName=role_name)

    def create_role(self, account_id, role_name, test_role_name):
        policy_doc = {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Effect': 'Allow',
                    'Principal': {'AWS': [f'arn:aws:iam::{account_id}:role/{test_role_name}']},
                    'Action': 'sts:AssumeRole',
                }
            ],
        }
        role = self._client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(policy_doc),
            Description='Role for Lambda function',
        )
        return role

    def get_consumption_role(self, account_id, role_name, test_role_name):
        role = self.get_role(role_name)
        if role is None:
            role = self.create_role(account_id, role_name, test_role_name)
            self.put_consumption_role_policy(role_name)
        return role

    def delete_policy(self, role_name, policy_name):
        self._client.delete_role_policy(RoleName=role_name, PolicyName=policy_name)

    def delete_consumption_role(self, role_name):
        self.delete_policy(role_name, self.CONSUMPTION_POLICY_NAME)
        self.delete_role(role_name)

    def put_consumption_role_policy(self, role_name):
        self._client.put_role_policy(
            RoleName=role_name,
            PolicyName=self.CONSUMPTION_POLICY_NAME,
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
