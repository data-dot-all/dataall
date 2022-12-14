import logging
import os


from backend.short_async_tasks import Worker
from backend.utils.aws import Ecs
from ...db import models
from ...utils import Parameter
from ...tasks.data_sharing.data_sharing_service import DataSharingService

log = logging.getLogger('aws:ecs')

##TODO: imake a better routing to long tasks, this piece between 17 and 27 could be an ECSRunner class

class ECSHandler:
    _instance = None

    @staticmethod
    def get_instance():
        if not ECSHandler._instance:
            ECSHandler._instance = ECSHandler()
        return ECSHandler._instance

    def __init__(self):
        self.tasks = {}
        self.enabled = True

    def queue(self, engine, task_ids: [str]):
        log.info(f'Queuing Task Ids: {task_ids}')

    def handler(self, path):
        def decorator(fn):
            self.tasks[path] = fn
            return fn

        return decorator

    @staticmethod
    def run_share_management_ecs_task(self, envname, share_uri, handler):
    share_task_definition = Parameter().get_parameter(
        env=envname, path='ecs/task_def_arn/share_management'
    )
    container_name = Parameter().get_parameter(
        env=envname, path='ecs/container/share_management'
    )
    cluster_name = Parameter().get_parameter(env=envname, path='ecs/cluster/name')
    subnets = Parameter().get_parameter(env=envname, path='ecs/private_subnets')
    security_groups = Parameter().get_parameter(
        env=envname, path='ecs/security_groups'
    )

    try:
        Ecs.run_ecs_task(
            cluster_name,
            share_task_definition,
            container_name,
            security_groups,
            subnets,
            [
                {'name': 'shareUri', 'value': share_uri},
                {'name': 'envname', 'value': envname},
                {'name': 'handler', 'value': handler},
                {
                    'name': 'AWS_REGION',
                    'value': os.getenv('AWS_REGION', 'eu-west-1'),
                },
            ],
        )
        return True
    except ClientError as e:
        log.error(e)
        raise e

ECSRunner = ECSHandler.get_instance()

class WorkerHandler:
    _instance = None

    @staticmethod
    def get_instance():
        if not WorkerHandler._instance:
            WorkerHandler._instance = WorkerHandler()
        return WorkerHandler._instance

    def __init__(self):
        self.handlers = {}
        self.enabled = True

    def queue(self, engine, task_ids: [str]):
        log.info(f'Queuing Task Ids: {task_ids}')

    def handler(self, path):
        def decorator(fn):
            self.handlers[path] = fn
            return fn

        return decorator

    def process(self, engine, task_ids: [str], save_response=True):
        tasks_responses = []
        if self.enabled:
            for taskid in task_ids:
                try:
                    log.info(f'Processing Worker Task: {taskid}')
                    handler, task = self.get_task_handler(engine, taskid)

                    error, response, status = self.handle_task(engine, task, handler)
                    if save_response:
                        WorkerHandler.update_task(
                            engine, taskid, error, to_json(response), status
                        )

                    else:
                        WorkerHandler.update_task(engine, taskid, error, {}, status)
                    tasks_responses.append(
                        {
                            'taskUri': taskid,
                            'response': response,
                            'error': error,
                            'status': status,
                        }
                    )
                    return tasks_responses
                except Exception as e:
                    print('==================>', e)
                    log.exception('Error in process')
                    log.error(f'Task processing failed {e} : {taskid}')
        else:
            log.info(f'Worker disabled, tasks {task_ids} wont be processed')

    def get_task_handler(self, engine, taskid):
        with engine.scoped_session() as session:
            task = session.query(Task).get(taskid)
            handler = self.handlers.get(task.action)
            log.info(
                f' found handler {handler} for task action {task.action}|{task.taskUri}'
            )
            if task.status != 'pending':
                raise Exception(
                    f'Could not start task {task.taskUri} as its status is {task.status}'
                )
            if not handler:
                raise Exception(f'No handler defined for {task.action}')
            task.status = 'started'
            session.commit()
        return handler, task

    @staticmethod
    def handle_task(engine, task: Task, handler):
        error = {}
        response = {}
        try:
            response = handler(engine, task)
            status = 'completed'
        except Exception as e:
            log.error(
                f'Failed to execute Task {task.taskUri} due to {e}', exc_info=True
            )
            error = {'message': str(e)}
            status = 'failed'
        return error, response, status

    @staticmethod
    def update_task(engine, taskid, error, response, status):
        with engine.scoped_session() as session:
            task = session.query(Task).get(taskid)
            task.status = status
            task.error = error
            task.response = response
            session.commit()
            return task

    @classmethod
    def retry(cls, exception, tries=4, delay=3, backoff=2, logger=None):
        """
        Retry calling the decorated function using an exponential backoff.
        :param exception: the exception to check. may be a tuple of
            exceptions to check
        :type exception: Exception or tuple
        :param tries: number of times to try (not retry) before giving up
        :type tries: int
        :param delay: initial delay between retries in seconds
        :type delay: int
        :param backoff: backoff multiplier e.g. value of 2 will double the delay
            each retry
        :type backoff: int
        :param logger: logger to use. If None, print
        :type logger: logging.Logger instance
        """

        def deco_retry(f):
            @wraps(f)
            def f_retry(*args, **kwargs):
                mtries, mdelay = tries, delay
                while mtries > 1:
                    try:
                        return f(*args, **kwargs)
                    except exception:
                        msg = f'Exception {str(exception)} was raised. Retrying in {mdelay} seconds...'
                        if logger:
                            logger.warning(msg)
                        else:
                            print(msg)
                        time.sleep(mdelay)
                        mtries -= 1
                        mdelay *= backoff
                return f(*args, **kwargs)

            return f_retry

        return deco_retry

