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
        cfn = CloudFormation.client(AwsAccountId=AwsAccountId, region=region)
        try:
            response = cfn.describe_stacks(StackName='CDKToolkit')
        except cfn.exceptions.ClientError as e:
            print(e)
            raise Exception('CDKToolkitNotFound')

        stacks = response['Stacks']
        if not len(stacks):
            raise Exception('CDKToolkitNotFound')

        try:
            response = cfn.describe_stack_resource(
                StackName='CDKToolkit', LogicalResourceId='CloudFormationExecutionRole'
            )
            cdk_role_name = response['StackResourceDetail']['PhysicalResourceId']
            return cdk_role_name
        except cfn.exceptions.ClientError as e:
            raise Exception('CDKToolkitDeploymentActionRoleNotFound')

    @staticmethod
    def delete_cloudformation_stack(**data):
        accountid = data['accountid']
        region = data['region']
        stack_name = data['stack_name']
        cdk_role_arn = data['cdk_role_arn']
        try:
            aws_session = SessionHelper.remote_session(accountid=accountid)
            cfnclient = aws_session.client('cloudformation', region_name=region)
            response = cfnclient.delete_stack(
                StackName=stack_name,
                RoleARN=cdk_role_arn,
                ClientRequestToken=str(uuid.uuid4()),
            )
            log.info(f'Stack {stack_name} deleted: {response}')
        except ClientError as e:
            log.error(f'Failed to delete stack {stack_name}')
            raise e

    @staticmethod
    def _get_stack(**data) -> dict:
        try:
            accountid = data['accountid']
            region = data['region']
            stack_name = data['stack_name']
            aws_session = SessionHelper.remote_session(accountid=accountid)
            cfnclient = aws_session.client('cloudformation', region_name=region)
            response = cfnclient.describe_stacks(StackName=stack_name)
            return response['Stacks'][0]
        except ClientError as e:
            raise e


    @staticmethod
    def _describe_stack_resources(**data):
        accountid = data['accountid']
        region = data.get('region', 'eu-west-1')
        stack_name = data['stack_name']
        aws_session = SessionHelper.remote_session(accountid=accountid)
        client = aws_session.client('cloudformation', region_name=region)
        try:
            stack_resources = client.describe_stack_resources(StackName=stack_name)
            log.info(f'Stack describe resources response : {stack_resources}')
            return stack_resources
        except ClientError as e:
            log.error(e, exc_info=True)

    @staticmethod
    def _describe_stack_events(**data):
        accountid = data['accountid']
        region = data.get('region', 'eu-west-1')
        stack_name = data['stack_name']
        aws_session = SessionHelper.remote_session(accountid=accountid)
        client = aws_session.client('cloudformation', region_name=region)
        try:
            stack_events = client.describe_stack_events(StackName=stack_name)
            log.info(f'Stack describe events response : {stack_events}')
            return stack_events
        except ClientError as e:
            log.error(e, exc_info=True)

