import logging
from botocore.exceptions import ClientError

from backend.short_async_tasks import Worker
from backend.aws import CloudFormation
from backend.utils import json_utils
from backend.db.common import models


log = logging.getLogger(__name__)


@Worker.handler(path='cloudformation.stack.delete')
def delete_stack(engine, task: models.Task):
    try:
        CloudFormation.delete_cloudformation_stack(
            AwsAccountId=task.payload['accountid'],
            region=task.payload['region'],
            stack_name=task.payload['stack_name'],
            cdk_role_arn=task.payload['cdk_role_arn']
        )
    except ClientError as e:
        log.error(f'Failed to delete CFN stack{task.targetUri}: {e}')
        raise e
    return {'status': 200, 'stackDeleted': True}


@Worker.handler(path='cloudformation.stack.status')
def get_stack_status(engine, task: models.Task):
    try:
        return CloudFormation.get_stack(
            AwsAccountId=task.payload['accountid'],
            region=task.payload['region'],
            stack_name=task.payload['stack_name']
        )['StackStatus']
    except ClientError as e:
        log.error(f'Failed to Get CFN stack status{task.targetUri}: {e}')
        raise e


@Worker.handler(path='cloudformation.stack.describe_resources')
def describe_stack_resources(engine, task: models.Task):
    try:
        filtered_resources = []
        filtered_events = []
        filtered_outputs = {}

        cfn_stack = CloudFormation.get_stack(
            AwsAccountId=task.payload['accountid'],
            region=task.payload['region'],
            stack_name=task.payload['stack_name']
        )
        stack_arn = cfn_stack['StackId']
        status = cfn_stack['StackStatus']
        stack_outputs = cfn_stack.get('Outputs', [])
        if stack_outputs:
            for output in stack_outputs:
                print(output)
                filtered_outputs[output['OutputKey']] = output['OutputValue']
        resources = CloudFormation.describe_stack_resources(
            AwsAccountId=task.payload['accountid'],
            region=task.payload['region'],
            stack_name=task.payload['stack_name']
        )['StackResources']
        events = CloudFormation.describe_stack_events(
            AwsAccountId=task.payload['accountid'],
            region=task.payload['region'],
            stack_name=task.payload['stack_name']
        )['StackEvents']
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



