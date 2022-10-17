import logging
import uuid

from botocore.exceptions import ClientError

from .service_handlers import Worker
from .sts import SessionHelper
from ...db import models, Engine
from ...utils import json_utils

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
    @Worker.handler(path='cloudformation.stack.delete')
    def delete_stack(engine, task: models.Task):
        try:
            data = {
                'accountid': task.payload['accountid'],
                'cdk_role_arn': task.payload['cdk_role_arn'],
                'region': task.payload['region'],
                'stack_name': task.payload['stack_name'],
            }
            CloudFormation.delete_cloudformation_stack(**data)
        except ClientError as e:
            log.error(f'Failed to delete CFN stack{task.targetUri}: {e}')
            raise e
        return {'status': 200, 'stackDeleted': True}

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
    @Worker.handler(path='cloudformation.stack.status')
    def get_stack_status(engine, task: models.Task):
        try:
            data = {
                'accountid': task.payload['accountid'],
                'region': task.payload['region'],
                'stack_name': task.payload['stack_name'],
            }
            return CloudFormation._get_stack(**data)['StackStatus']
        except ClientError as e:
            log.error(f'Failed to Get CFN stack status{task.targetUri}: {e}')
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
    @Worker.handler(path='cloudformation.stack.describe_resources')
    def describe_stack_resources(engine, task: models.Task):
        try:
            filtered_resources = []
            filtered_events = []
            filtered_outputs = {}
            data = {
                'accountid': task.payload['accountid'],
                'region': task.payload['region'],
                'stack_name': task.payload['stack_name'],
            }

            cfn_stack = CloudFormation._get_stack(**data)
            stack_arn = cfn_stack['StackId']
            status = cfn_stack['StackStatus']
            stack_outputs = cfn_stack.get('Outputs', [])
            if stack_outputs:
                for output in stack_outputs:
                    print(output)
                    filtered_outputs[output['OutputKey']] = output['OutputValue']
            resources = CloudFormation._describe_stack_resources(**data)[
                'StackResources'
            ]
            events = CloudFormation._describe_stack_events(**data)['StackEvents']
            with engine.scoped_session() as session:
                stack: models.Stack = session.query(models.Stack).get(
                    task.payload['stackUri']
                )
                stack.status = status
                stack.stackid = stack_arn
                stack.outputs = filtered_outputs
                for resource in resources:
                    filtered_resources.append(
                        {
                            'ResourceStatus': resource.get('ResourceStatus'),
                            'LogicalResourceId': resource.get('LogicalResourceId'),
                            'PhysicalResourceId': resource.get('PhysicalResourceId'),
                            'ResourceType': resource.get('ResourceType'),
                            'StackName': resource.get('StackName'),
                            'StackId': resource.get('StackId'),
                        }
                    )
                stack.resources = {'resources': filtered_resources}
                for event in events:
                    filtered_events.append(
                        {
                            'ResourceStatus': event.get('ResourceStatus'),
                            'LogicalResourceId': event.get('LogicalResourceId'),
                            'PhysicalResourceId': event.get('PhysicalResourceId'),
                            'ResourceType': event.get('ResourceType'),
                            'StackName': event.get('StackName'),
                            'StackId': event.get('StackId'),
                            'EventId': event.get('EventId'),
                            'ResourceStatusReason': event.get('ResourceStatusReason'),
                        }
                    )
                stack.events = {'events': filtered_events}
                stack.error = None
                session.commit()
        except ClientError as e:
            with engine.scoped_session() as session:
                stack: models.Stack = session.query(models.Stack).get(
                    task.payload['stackUri']
                )
                if not stack.error:
                    stack.error = {
                        'error': json_utils.to_string(e.response['Error']['Message'])
                    }
                session.commit()

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


@Worker.handler(path='environment.check.cdk.boostrap')
def check_cdk_boostrap(engine: Engine, task: models.Task):
    with engine.scoped_session() as session:
        account = task.payload.get('account')
        region = task.payload.get('region')
        aws = SessionHelper.remote_session(accountid=account)
        cfn = aws.client('cloudformation', region_name=region)
        response = cfn.describe_stacks(StackName='CDKToolkit')
        stacks = response['Stacks']
        if len(stacks):
            return True
        else:
            return False
