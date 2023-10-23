import os
import logging
import boto3

from dataall.base.utils.IdentityProvider import IdentityProvider

log = logging.getLogger(__name__)


class Cognito(IdentityProvider):

    def __init__(self):
        self.client = boto3.client('cognito-idp', region_name=os.getenv('AWS_REGION', 'eu-west-1'))

    def get_user_emailids_from_group(self, groupName):
        try:
            envname = os.getenv('envname', 'local')
            parameter_path = f'/dataall/{envname}/cognito/userpool'
            ssm = boto3.client('ssm', region_name=os.getenv('AWS_REGION', 'eu-west-1'))
            user_pool_id = ssm.get_parameter(Name=parameter_path)['Parameter']['Value']
            cognito_user_list = self.client.list_users_in_group(UserPoolId=user_pool_id, GroupName=groupName)["Users"]
            group_email_ids = []
            attributes = []
            # Make a flat list
            [attributes.extend(x['Attributes']) for x in cognito_user_list]
            # Extract all the email-ids
            group_email_ids.extend([x['Value'] for x in attributes if x['Name'] == 'email'])

        except Exception as e:
            log.error(
                f'Failed to get email ids for Cognito group {groupName} due to {e}'
            )
            raise e
        else:
            return group_email_ids

    @staticmethod
    def list_cognito_groups(envname: str, region: str):
        try:
            parameter_path = f'/dataall/{envname}/cognito/userpool'
            ssm = boto3.client('ssm', region_name=region)
            user_pool_id = ssm.get_parameter(Name=parameter_path)['Parameter']['Value']
            cognito = boto3.client('cognito-idp', region_name=region)
            groups = cognito.list_groups(UserPoolId=user_pool_id)['Groups']
        except Exception as e:
            log.error(
                f'Failed to list groups of user pool {user_pool_id} due to {e}'
            )
        else:
            return groups
