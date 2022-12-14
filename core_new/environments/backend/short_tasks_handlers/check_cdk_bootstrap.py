import logging

from backend.short_async_tasks import Worker
from backend.utils.aws.sts import SessionHelper
from backend.db import Engine, common

log = logging.getLogger(__name__)

@Worker.handler(path='environment.check.cdk.boostrap')
def check_cdk_boostrap(engine: Engine, task: common.models.Task):
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
