# This  module is a wrapper for the cdk cli
# Python native subprocess package is used to spawn cdk [deploy|destroy] commands with appropriate parameters.
# Additionally, it uses the cdk plugin cdk-assume-role-credential-plugin to run cdk commands on target accounts
# see : https://github.com/aws-samples/cdk-assume-role-credential-plugin

import logging
import os
import subprocess
import sys
import ast

import boto3
from botocore.exceptions import ClientError

from ..aws.handlers.sts import SessionHelper
from ..db import Engine
from ..db import models
from ..db.api import Pipeline, Environment, Stack
from ..utils.alarm_service import AlarmService
from dataall.cdkproxy.cdkpipeline.cdk_pipeline import CDKPipelineStack

logger = logging.getLogger('cdksass')

ENVNAME = os.getenv('envname', 'local')


def aws_configure(profile_name='default'):
    print('..............................................')
    print('        Running configure                     ')
    print('..............................................')
    print(f"AWS_CONTAINER_CREDENTIALS_RELATIVE_URI: {os.getenv('AWS_CONTAINER_CREDENTIALS_RELATIVE_URI')}")
    cmd = ['curl', '169.254.170.2$AWS_CONTAINER_CREDENTIALS_RELATIVE_URI']
    process = subprocess.run(' '.join(cmd), text=True, shell=True, encoding='utf-8', capture_output=True)  # nosec
    creds = None
    if process.returncode == 0:
        creds = ast.literal_eval(process.stdout)

    return creds


def update_stack_output(session, stack):
    outputs = {}
    stack_outputs = None
    aws = SessionHelper.remote_session(stack.accountid)
    cfn = aws.resource('cloudformation', region_name=stack.region)
    try:
        stack_outputs = cfn.Stack(f'{stack.name}').outputs
    except ClientError as e:
        logger.warning(f'Failed to retrieve stack output for stack {stack.name} due to: {e}')
    if stack_outputs:
        for output in stack_outputs:
            outputs[output['OutputKey']] = output['OutputValue']
        stack.outputs = outputs


def deploy_cdk_stack(engine: Engine, stackid: str, app_path: str = None, path: str = None):
    logger.warning(f'Starting new stack from  stackid {stackid}')
    sts = boto3.client('sts')
    idnty = sts.get_caller_identity()
    this_aws_account = idnty['Account']
    creds = None
    if ENVNAME not in ['local', 'dkrcompose']:
        creds = aws_configure()

    with engine.scoped_session() as session:
        try:
            stack: models.Stack = session.query(models.Stack).get(stackid)
            logger.warning(f'stackuri = {stack.stackUri}, stackId = {stack.stackid}')
            stack.status = 'PENDING'
            session.commit()

            if stack.stack == 'cdkpipeline':
                cdkpipeline = CDKPipelineStack(stack.targetUri)
                venv_name = cdkpipeline.venv_name if cdkpipeline.venv_name else None
                pipeline = Pipeline.get_pipeline_by_uri(session, stack.targetUri)
                path = f'./cdkpipeline/{pipeline.repo}/'
                app_path = './app.py'
                if not venv_name:
                    logger.info('Successfully Updated CDK Pipeline')
                    meta = describe_stack(stack)
                    stack.stackid = meta['StackId']
                    stack.status = meta['StackStatus']
                    update_stack_output(session, stack)
                    return

            cwd = (
                os.path.join(os.path.dirname(os.path.abspath(__file__)), path)
                if path
                else os.path.dirname(os.path.abspath(__file__))
            )
            python_path = '/:'.join(sys.path)[1:] + ':/code'
            logger.info(f'python path = {python_path}')

            env = {
                'AWS_REGION': os.getenv('AWS_REGION', 'eu-west-1'),
                'AWS_DEFAULT_REGION': os.getenv('AWS_REGION', 'eu-west-1'),
                'PYTHONPATH': python_path,
                'CURRENT_AWS_ACCOUNT': this_aws_account,
                'envname': os.environ.get('envname', 'local'),
            }
            if creds:
                env.update(
                    {
                        'AWS_ACCESS_KEY_ID': creds.get('AccessKeyId'),
                        'AWS_SECRET_ACCESS_KEY': creds.get('SecretAccessKey'),
                        'AWS_SESSION_TOKEN': creds.get('Token'),
                    }
                )

            app_path = app_path or './app.py'

            logger.info(f'app_path: {app_path}')
            cmd = [
                '' '. ~/.nvm/nvm.sh &&',
                'cdk',
                'deploy --all',
                '--require-approval',
                ' never',
                '-c',
                f"appid='{stack.name}'",
                # the target accountid
                '-c',
                f"account='{stack.accountid}'",
                # the target region
                '-c',
                f"region='{stack.region}'",
                # the predefined stack
                '-c',
                f"stack='{stack.stack}'",
                # the payload for the stack with additional parameters
                '-c',
                f"target_uri='{stack.targetUri}'",
                '-c',
                "data='{}'",
                # skips synth step when no changes apply
                '--app',
                f'"{sys.executable} {app_path}"',
                '--verbose',
            ]

            if stack.stack == 'cdkpipeline':
                aws = SessionHelper.remote_session(stack.accountid)
                creds = aws.get_credentials()
                env.update(
                    {
                        'CDK_DEFAULT_REGION': stack.region,
                        'AWS_REGION': stack.region,
                        'AWS_DEFAULT_REGION': stack.region,
                        'CDK_DEFAULT_ACCOUNT': stack.accountid,
                        'AWS_ACCESS_KEY_ID': creds.access_key,
                        'AWS_SECRET_ACCESS_KEY': creds.secret_key,
                        'AWS_SESSION_TOKEN': creds.token,
                    }
                )

            logger.info(f"Running command : \n {' '.join(cmd)}")

            process = subprocess.run(
                ' '.join(cmd),
                text=True,
                shell=True,  # nosec
                encoding='utf-8',
                env=env,
                cwd=cwd,
            )
            if stack.stack == 'cdkpipeline':
                CDKPipelineStack.clean_up_repo(path=f'./{pipeline.repo}')

            if process.returncode == 0:
                meta = describe_stack(stack)
                stack.stackid = meta['StackId']
                stack.status = meta['StackStatus']
                update_stack_output(session, stack)
            else:
                stack.status = 'CREATE_FAILED'
                logger.error(f'Failed to deploy stack {stackid} due to {str(process.stderr)}')
                AlarmService().trigger_stack_deployment_failure_alarm(stack=stack)

        except Exception as e:
            logger.error(f'Failed to deploy stack {stackid} due to {e}')
            AlarmService().trigger_stack_deployment_failure_alarm(stack=stack)
            raise e


def describe_stack(stack, engine: Engine = None, stackid: str = None):
    if not stack:
        with engine.scoped_session() as session:
            stack = session.query(models.Stack).get(stackid)
    if stack.status == 'DELETE_COMPLETE':
        return {'StackId': stack.stackid, 'StackStatus': stack.status}
    session = SessionHelper.remote_session(stack.accountid)
    resource = session.resource('cloudformation', region_name=stack.region)
    try:
        meta = resource.Stack(f'{stack.name}')
        return {'StackId': meta.stack_id, 'StackStatus': meta.stack_status}
    except ClientError as e:
        logger.warning(f'Failed to retrieve stack output for stack {stack.name} due to: {e}')
        meta = resource.Stack(stack.stackid)
        return {'StackId': meta.stack_id, 'StackStatus': meta.stack_status}


def cdk_installed():
    cmd = ['. ~/.nvm/nvm.sh && cdk', '--version']
    logger.info(f"Running command {' '.join(cmd)}")

    subprocess.run(
        cmd,
        text=True,
        shell=True,  # nosec
        encoding='utf-8',
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=os.path.dirname(__file__),
    )


if __name__ == '__main__':
    print(aws_configure())
