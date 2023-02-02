import logging

from backend.short_async_tasks import Worker
from backend.aws.cloudformation import CloudFormation
from backend.db import Engine, common

log = logging.getLogger(__name__)

@Worker.handler(path='environment.check.cdk.boostrap')
def check_cdk_boostrap(engine: Engine, task: common.models.Task):
    with engine.scoped_session() as session:
        account = task.payload.get('account')
        region = task.payload.get('region')
        cfn = CloudFormation.client(accountid=account, region=region) ##TODO change this call for CloudFormation class method
        response = cfn.describe_stacks(StackName='CDKToolkit')
        stacks = response['Stacks']
        if len(stacks):
            return True
        else:
            return False
