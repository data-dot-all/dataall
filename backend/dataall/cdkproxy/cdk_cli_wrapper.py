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

logger = logging.getLogger('cdksass')

ENVNAME = os.getenv('envname', 'local')


def aws_configure(profile_name='default'):
    print('..............................................')
    print('        Running configure                     ')
    print('..............................................')
    print(f"AWS_CONTAINER_CREDENTIALS_RELATIVE_URI: {os.getenv('AWS_CONTAINER_CREDENTIALS_RELATIVE_URI')}")
    cmd = [
        'curl',
        '169.254.170.2$AWS_CONTAINER_CREDENTIALS_RELATIVE_URI'
    ]
    process = subprocess.run(
        ' '.join(cmd),
        text=True,
        shell=True,  # nosec
        encoding='utf-8',
        capture_output=True
    )
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
        logger.warning(
            f'Failed to retrieve stack output for stack {stack.name} due to: {e}'
        )
    if stack_outputs:
        for output in stack_outputs:
            outputs[output['OutputKey']] = output['OutputValue']
        stack.outputs = outputs


def clone_remote_stack(pipeline, pipeline_environment):
    print('..................................................')
    print('     Configure remote CDK app                     ')
    print('..................................................')
    aws = SessionHelper.remote_session(pipeline_environment.AwsAccountId)
    env_creds = aws.get_credentials()

    python_path = '/:'.join(sys.path)[1:] + ':/code' + os.getenv('PATH')

    env = {
        'AWS_REGION': pipeline_environment.region,
        'AWS_DEFAULT_REGION': pipeline_environment.region,
        'CURRENT_AWS_ACCOUNT': pipeline_environment.AwsAccountId,
        'PYTHONPATH': python_path,
        'PATH': python_path,
        'envname': os.environ.get('envname', 'local'),
    }
    if env_creds:
        env.update(
            {
                'AWS_ACCESS_KEY_ID': env_creds.access_key,
                'AWS_SECRET_ACCESS_KEY': env_creds.secret_key,
                'AWS_SESSION_TOKEN': env_creds.token,
            }
        )
    print(f"ENVIRONMENT = {env}")
    print('..................................................')
    print('        Clone remote CDK app                      ')
    print('..................................................')

    cmd = [
        'git',
        'config',
        '--system',
        'user.name',
        'data.allECS',
        '&&',
        'git',
        'config',
        '--system',
        'user.email',
        'data.allECS@email.com',
        '&&',
        'cd',
        'dataall/cdkproxy/stacks',
        '&&',
        'mkdir',
        f'{pipeline.repo}',
        '&&',
        'git',
        'clone',
        f"codecommit::{pipeline_environment.region}://{pipeline.repo}",
        f'{pipeline.repo}'
    ]
    process = subprocess.run(
        ' '.join(cmd),
        text=True,
        shell=True,  # nosec
        encoding='utf-8',
        capture_output=True,
        env=env
    )
    if process.returncode == 0:
        print(f"Successfully cloned repo {pipeline.repo}: {str(process.stdout)}")
    else:
        logger.error(
            f'Failed to clone repo {pipeline.repo} due to {str(process.stderr)}'
        )
    return


def clean_up_repo(path):
    if path:
        precmd = [
            'rm',
            '-rf',
            f"{path}"
        ]

        cwd = os.path.dirname(os.path.abspath(__file__))
        logger.info(f"Running command : \n {' '.join(precmd)}")

        process = subprocess.run(
            ' '.join(precmd),
            text=True,
            shell=True,  # nosec
            encoding='utf-8',
            capture_output=True,
            cwd=cwd
        )

        if process.returncode == 0:
            print(f"Successfully cleaned cloned repo: {path}. {str(process.stdout)}")
        else:
            logger.error(
                f'Failed clean cloned repo: {path} due to {str(process.stderr)}'
            )
    else:
        logger.info(f"Info:Path {path} not found")
    return


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
            logger.warning(f"stackuri = {stack.stackUri}, stackId = {stack.stackid}")
            stack.status = 'PENDING'
            session.commit()

            app_path = app_path or './app.py'

            logger.info(f'app_path: {app_path}')

            cmd = [
                ''
                '. ~/.nvm/nvm.sh &&',
                'cdk',
                'deploy',
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
            logger.info(f"Running command : \n {' '.join(cmd)}")

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

            cwd = os.path.join(os.path.dirname(os.path.abspath(__file__)), path) if path else os.path.dirname(os.path.abspath(__file__))

            process = subprocess.run(
                ' '.join(cmd),
                text=True,
                shell=True,  # nosec
                encoding='utf-8',
                env=env,
                cwd=cwd,
            )

            if process.returncode == 0:
                meta = describe_stack(stack)
                stack.stackid = meta['StackId']
                stack.status = meta['StackStatus']
                update_stack_output(session, stack)
                if stack.stack == 'cdkrepo':
                    logger.warning(f'Starting new remote stack from  targetUri {stack.targetUri}pip')
                    cicdstack: models.Stack = Stack.get_stack_by_target_uri(session, target_uri=f"{stack.targetUri}pip")
                    cicdstack.EcsTaskArn = stack.EcsTaskArn
                    session.commit()
                    pipeline = Pipeline.get_pipeline_by_uri(session, stack.targetUri)
                    pipeline_environment = Environment.get_environment_by_uri(session, pipeline.environmentUri)
                    clone_remote_stack(pipeline, pipeline_environment)
                    deploy_cdk_stack(engine, cicdstack.stackUri, app_path="app.py", path=f"./stacks/{pipeline.repo}/")
                    clean_up_repo(f"./stacks/{pipeline.repo}")
            else:
                stack.status = 'CREATE_FAILED'
                logger.error(
                    f'Failed to deploy stack {stackid} due to {str(process.stderr)}'
                )
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
        logger.warning(
            f'Failed to retrieve stack output for stack {stack.name} due to: {e}'
        )
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
