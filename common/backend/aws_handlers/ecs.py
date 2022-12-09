import logging

import boto3
from botocore.exceptions import ClientError


log = logging.getLogger('aws:ecs')


class Ecs:
    def __init__(self):
        pass

    @staticmethod
    def run_ecs_task(
        cluster_name,
        task_definition,
        container_name,
        security_groups,
        subnets,
        environment,
        started_by='awsworker',
    ):
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
                        'environment': environment,
                    }
                ]
            },
            startedBy=started_by,
        )
        if response['failures']:
            raise Exception(
                ', '.join(
                    [
                        'fail to run task {0} reason: {1}'.format(
                            failure['arn'], failure['reason']
                        )
                        for failure in response['failures']
                    ]
                )
            )
        task_arn = response.get('tasks', [{'taskArn': None}])[0]['taskArn']
        log.info(f'Task started {task_arn}..')
        return task_arn

    @staticmethod
    def is_task_running(cluster_name, started_by):
        try:
            client = boto3.client('ecs')
            running_tasks = client.list_tasks(
                cluster=cluster_name, startedBy=started_by, desiredStatus='RUNNING'
            )
            if running_tasks and running_tasks.get('taskArns'):
                return True
            return False
        except ClientError as e:
            log.error(e)
            raise e
