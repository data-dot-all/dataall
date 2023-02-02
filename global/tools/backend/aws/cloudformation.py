import logging
import uuid
from botocore.exceptions import ClientError

from .sts import SessionHelper

log = logging.getLogger(__name__)


class CloudFormation:
    def __init__(self):
        pass

    @staticmethod
    def client(AwsAccountId, region):
        session = SessionHelper.remote_session(AwsAccountId)
        return session.client('cloudformation', region_name=region)

    @staticmethod
    def check_existing_cdk_toolkit_stack(AwsAccountId, region):
        cfn_client = CloudFormation.client(AwsAccountId=AwsAccountId, region=region)
        try:
            response = cfn_client.describe_stacks(StackName='CDKToolkit')
        except cfn_client.exceptions.ClientError as e:
            print(e)
            raise Exception('CDKToolkitNotFound')

        stacks = response['Stacks']
        if not len(stacks):
            raise Exception('CDKToolkitNotFound')

        try:
            response = cfn_client.describe_stack_resource(
                StackName='CDKToolkit', LogicalResourceId='CloudFormationExecutionRole'
            )
            cdk_role_name = response['StackResourceDetail']['PhysicalResourceId']
            return cdk_role_name
        except cfn_client.exceptions.ClientError as e:
            raise Exception('CDKToolkitDeploymentActionRoleNotFound')

    @staticmethod
    def delete_cloudformation_stack(AwsAccountId, region, stack_name, cdk_role_arn):
        try:
            cfn_client = CloudFormation.client(AwsAccountId=AwsAccountId, region=region)
            response = cfn_client.delete_stack(
                StackName=stack_name,
                RoleARN=cdk_role_arn,
                ClientRequestToken=str(uuid.uuid4()),
            )
            log.info(f'Stack {stack_name} deleted: {response}')
        except ClientError as e:
            log.error(f'Failed to delete stack {stack_name}')
            raise e

    @staticmethod
    def get_stack(AwsAccountId, region, stack_name):
        try:
            cfn_client = CloudFormation.client(AwsAccountId=AwsAccountId, region=region)
            response = cfn_client.describe_stacks(StackName=stack_name)
            return response['Stacks'][0]
        except ClientError as e:
            raise e


    @staticmethod
    def describe_stack_resources(AwsAccountId, region, stack_name):
        cfn_client = CloudFormation.client(AwsAccountId=AwsAccountId, region=region)
        try:
            stack_resources = cfn_client.describe_stack_resources(StackName=stack_name)
            log.info(f'Stack describe resources response : {stack_resources}')
            return stack_resources
        except ClientError as e:
            log.error(e, exc_info=True)

    @staticmethod
    def describe_stack_events(AwsAccountId, region, stack_name):
        cfn_client = CloudFormation.client(AwsAccountId=AwsAccountId, region=region)
        try:
            stack_events = cfn_client.describe_stack_events(StackName=stack_name)
            log.info(f'Stack describe events response : {stack_events}')
            return stack_events
        except ClientError as e:
            log.error(e, exc_info=True)

