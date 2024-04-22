import logging
import os
import time
from functools import wraps

from dataall.core.tasks.db.task_models import Task
from dataall.base.utils.json_utils import to_json

log = logging.getLogger(__name__)
ENVNAME = os.getenv('envname', 'local')


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
                    log.info(f'Processing Task: {taskid}')
                    handler, task = self.get_task_handler(engine, taskid)

                    error, response, status = self.handle_task(engine, task, handler)
                    if save_response:
                        WorkerHandler.update_task(engine, taskid, error, to_json(response), status)

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
                    log.exception('Error in process')
                    log.error(f'Task processing failed {e} : {taskid}')
        else:
            log.info(f'Worker disabled, tasks {task_ids} wont be processed')

    def get_task_handler(self, engine, taskid):
        with engine.scoped_session() as session:
            task = session.query(Task).get(taskid)
            handler = self.handlers.get(task.action)
            log.info(f' found handler {handler} for task action {task.action}|{task.taskUri}')
            if task.status != 'pending':
                raise Exception(f'Could not start task {task.taskUri} as its status is {task.status}')
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
            log.error(f'Failed to execute Task {task.taskUri} due to {e}', exc_info=True)
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


Worker = WorkerHandler.get_instance()
