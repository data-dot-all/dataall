import logging
import os

import boto3
from botocore.exceptions import ClientError

from dataall.base.utils import Parameter

log = logging.getLogger('aws:ecs')


class Ecs:
    def __init__(self):
        pass

    @staticmethod
    def run_cdkproxy_task(stack_uri):
        task_arn = Ecs.run_ecs_task(
            task_definition_param='ecs/task_def_arn/cdkproxy',
            container_name_param='ecs/container/cdkproxy',
            context=[{'name': 'stackUri', 'value': stack_uri}],
            started_by=f'awsworker-{stack_uri}',
        )
        log.info(f'ECS Task {task_arn} running')
        return task_arn

    @staticmethod
    def run_ecs_task(
        task_definition_param,
        container_name_param,
        context,
        started_by='awsworker',
    ):
        try:
            envname = os.environ.get('envname', 'local')
            cluster_name = Parameter().get_parameter(env=envname, path='ecs/cluster/name')
            subnets = Parameter().get_parameter(env=envname, path='ecs/private_subnets')
            security_groups = Parameter().get_parameter(env=envname, path='ecs/security_groups')

            task_definition = Parameter().get_parameter(env=envname, path=task_definition_param)
            container_name = Parameter().get_parameter(env=envname, path=container_name_param)

            response = boto3.client('ecs').run_task(
                cluster=cluster_name,
                taskDefinition=task_definition,
                count=1,
                launchType='FARGATE',
                networkConfiguration={
                    'awsvpcConfiguration': {
                        'subnets': subnets.split(','),
                        'securityGroups': security_groups.split(','),
                    }
                },
                overrides={
                    'containerOverrides': [
                        {
                            'name': container_name,
                            'environment': [
                                {'name': 'config_location', 'value': '/config.json'},
                                {'name': 'envname', 'value': envname},
                                {
                                    'name': 'AWS_REGION',
                                    'value': os.getenv('AWS_REGION', 'eu-west-1'),
                                },
                                *context,
                            ],
                        }
                    ]
                },
                startedBy=started_by,
            )
            if response['failures']:
                raise Exception(
                    ', '.join(
                        [
                            'fail to run task {0} reason: {1}'.format(failure['arn'], failure['reason'])
                            for failure in response['failures']
                        ]
                    )
                )
            task_arn = response.get('tasks', [{'taskArn': None}])[0]['taskArn']
            log.info(f'Task started {task_arn}..')
            return task_arn
        except ClientError as e:
            log.error(e)
            raise e

    @staticmethod
    def is_task_running(cluster_name, started_by=None):
        try:
            client = boto3.client('ecs')
            if started_by is None:
                running_tasks = client.list_tasks(cluster=cluster_name, desiredStatus='RUNNING')
            else:
                running_tasks = client.list_tasks(cluster=cluster_name, startedBy=started_by, desiredStatus='RUNNING')
            if running_tasks and running_tasks.get('taskArns'):
                return True
            return False
        except ClientError as e:
            log.error(e)
            raise e
