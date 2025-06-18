# This  module is a wrapper for the cdk cli
# Python native subprocess package is used to spawn cdk [deploy|destroy] commands with appropriate parameters.
# Additionally, it uses the cdk plugin cdk-assume-role-credential-plugin to run cdk commands on target accounts
# see : https://github.com/aws-samples/cdk-assume-role-credential-plugin

import ast
import logging
import os
import subprocess
import sys
from abc import abstractmethod
from typing import Dict

import boto3
from botocore.exceptions import ClientError

from dataall.core.stacks.db.stack_models import Stack
from dataall.base.aws.sts import SessionHelper
from dataall.base.db import Engine
from dataall.base.utils.alarm_service import AlarmService
from dataall.base.utils.shell_utils import CommandSanitizer

logger = logging.getLogger('cdksass')

ENVNAME = os.getenv('envname', 'local')


class CDKCliWrapperExtension:
    def __init__(self):
        pass

    @abstractmethod
    def extend_deployment(self, stack, session, env):
        raise NotImplementedError('Method extend_deployment is not implemented')

    @abstractmethod
    def post_deployment(self):
        raise NotImplementedError('Method post_deployment is not implemented')


_CDK_CLI_WRAPPER_EXTENSIONS: Dict[str, CDKCliWrapperExtension] = {}


def aws_configure(profile_name='default'):
    print('..............................................')
    print('        Running configure                     ')
    print('..............................................')
    AWS_CONTAINER_CREDENTIALS_RELATIVE_URI = os.getenv('AWS_CONTAINER_CREDENTIALS_RELATIVE_URI')
    cmd = ['curl', f'169.254.170.2{AWS_CONTAINER_CREDENTIALS_RELATIVE_URI}']
    process = subprocess.run(cmd, text=True, shell=False, encoding='utf-8', capture_output=True)
    creds = None
    if process.returncode == 0:
        creds = ast.literal_eval(process.stdout)
    else:
        logger.error(f'Failed clean curl credentials due to {str(process.stderr)}')

    return creds


def update_stack_output(session, stack):
    outputs = {}
    stack_outputs = None
    aws = SessionHelper.remote_session(stack.accountid, stack.region)
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
    from dataall.base.loader import load_modules, ImportMode

    load_modules(modes={ImportMode.CDK_CLI_EXTENSION})
    logger.warning(f'Starting new stack from  stackid {stackid}')
    region = os.getenv('AWS_REGION', 'eu-west-1')
    sts = boto3.client('sts', region_name=region, endpoint_url=f'https://sts.{region}.amazonaws.com')
    idnty = sts.get_caller_identity()
    this_aws_account = idnty['Account']
    creds = None
    if ENVNAME not in ['local', 'dkrcompose']:
        creds = aws_configure()

    with engine.scoped_session() as session:
        try:
            stack: Stack = session.query(Stack).get(stackid)
            logger.warning(f'stackuri = {stack.stackUri}, stackId = {stack.stackid}')
            stack.status = 'PENDING'
            session.commit()

            python_path = '/:'.join(sys.path)[1:] + ':/code'
            logger.info(f'python path = {python_path}')

            env = {
                'AWS_REGION': os.getenv('AWS_REGION', 'eu-west-1'),
                'AWS_DEFAULT_REGION': os.getenv('AWS_REGION', 'eu-west-1'),
                'PYTHONPATH': python_path,
                'CURRENT_AWS_ACCOUNT': this_aws_account,
                'envname': os.environ.get('envname', 'local'),
                'config_location': '/config.json',
            }
            if creds:
                env.update(
                    {
                        'AWS_ACCESS_KEY_ID': creds.get('AccessKeyId'),
                        'AWS_SECRET_ACCESS_KEY': creds.get('SecretAccessKey'),
                        'AWS_SESSION_TOKEN': creds.get('Token'),
                    }
                )

            extension = _CDK_CLI_WRAPPER_EXTENSIONS.get(stack.stack)
            if extension:
                logger.info(f'Extending CDK deployment process with steps for the following stack: {stack.stack}')
                finish_deployment, path, app_path = _CDK_CLI_WRAPPER_EXTENSIONS[stack.stack].extend_deployment(
                    stack=stack, session=session, env=env
                )
                if finish_deployment:
                    return
            else:
                logger.info(
                    f'There is no CDK deployment extension for {stack.stack}. Proceeding further with the deployment'
                )

            cwd = path if path else os.path.dirname(os.path.abspath(__file__))

            app_path = app_path or './app.py'

            logger.info(f'app_path: {app_path}')
            input_args = [stack.name, stack.accountid, stack.region, stack.stack, stack.targetUri]

            CommandSanitizer(input_args)

            cmd = [
                '. ~/.nvm/nvm.sh &&',
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
            logger.info(f'Running command : \n {" ".join(cmd)}')

            # This command is too complex to be executed as a list of commands. We need to run it with shell=True
            # However, the input arguments have to be sanitized with the CommandSanitizer

            process = subprocess.run(  # nosemgrep
                ' '.join(cmd),  # nosemgrep
                text=True,  # nosemgrep
                shell=True,  # nosec  # nosemgrep
                encoding='utf-8',  # nosemgrep
                env=env,  # nosemgrep
                cwd=cwd,  # nosemgrep
            )

            if extension:
                _CDK_CLI_WRAPPER_EXTENSIONS[stack.stack].post_deployment()
            else:
                logger.info(
                    f'There is no CDK deployment extension for {stack.stack}. Proceeding further with the post-deployment'
                )

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
            stack = session.query(Stack).get(stackid)
    if stack.status == 'DELETE_COMPLETE':
        return {'StackId': stack.stackid, 'StackStatus': stack.status}
    session = SessionHelper.remote_session(stack.accountid, stack.region)
    resource = session.resource('cloudformation', region_name=stack.region)
    try:
        meta = resource.Stack(f'{stack.name}')
        return {'StackId': meta.stack_id, 'StackStatus': meta.stack_status}
    except ClientError as e:
        logger.warning(f'Failed to retrieve stack output for stack {stack.name} due to: {e}')
        meta = resource.Stack(stack.stackid)
        return {'StackId': meta.stack_id, 'StackStatus': meta.stack_status}


def cdk_installed():
    cmd1 = ['.', '~/.nvm/nvm.sh']
    logger.info(f'Running command {" ".join(cmd1)}')
    subprocess.run(
        cmd1,
        text=True,
        shell=False,
        encoding='utf-8',
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=os.path.dirname(__file__),
    )

    cmd2 = ['cdk', '--version']
    logger.info(f'Running command {" ".join(cmd2)}')
    subprocess.run(
        cmd2,
        text=True,
        shell=False,
        encoding='utf-8',
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=os.path.dirname(__file__),
    )


if __name__ == '__main__':
    print(aws_configure())
