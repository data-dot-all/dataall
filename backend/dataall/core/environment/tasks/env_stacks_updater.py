import logging
import os
import sys
import time

from dataall.base.loader import ImportMode, load_modules
from dataall.core.environment.db.environment_models import Environment
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.environment.tasks.env_stack_finder import StackFinder
from dataall.core.stacks.aws.ecs import Ecs
from dataall.core.stacks.db.stack_repositories import StackRepository
from dataall.base.db import get_engine
from dataall.base.utils import Parameter

log = logging.getLogger(__name__)


RETRIES = 30
SLEEP_TIME = 30


def update_stacks(engine, envname):
    with engine.scoped_session() as session:
        all_environments: [Environment] = EnvironmentService.list_all_active_environments(session)
        additional_stacks = []
        for finder in StackFinder.all():
            additional_stacks.extend(finder.find_stack_uris(session))

        log.info(f'Found {len(all_environments)} environments, triggering update stack tasks...')
        environment: Environment
        for environment in all_environments:
            update_stack(session=session, envname=envname, target_uri=environment.environmentUri, wait=True)

        for stack_uri in additional_stacks:
            update_stack(session=session, envname=envname, target_uri=stack_uri, wait=False)

        return len(all_environments), len(additional_stacks)


def update_stack(session, envname, target_uri, wait=False):
    stack = StackRepository.get_stack_by_target_uri(session, target_uri=target_uri)
    cluster_name = Parameter().get_parameter(env=envname, path='ecs/cluster/name')
    if not Ecs.is_task_running(cluster_name=cluster_name, started_by=f'awsworker-{stack.stackUri}'):
        stack.EcsTaskArn = Ecs.run_cdkproxy_task(stack_uri=stack.stackUri)
        if wait:
            retries = 1
            while Ecs.is_task_running(cluster_name=cluster_name, started_by=f'awsworker-{stack.stackUri}'):
                log.info(
                    f'Update for {stack.name}//{stack.stackUri} is not complete, waiting for {SLEEP_TIME} seconds...'
                )
                time.sleep(SLEEP_TIME)
                retries = retries + 1
                if retries > RETRIES:
                    log.info(f'Maximum number of retries exceeded ({RETRIES} retries), continuing task...')
                    break
            log.info(
                f'Update for {stack.name}//{stack.stackUri} COMPLETE or maximum number of retries exceeded ({RETRIES} retries)'
            )
    else:
        log.info(f'Stack update is already running... Skipping stack {stack.name}//{stack.stackUri}')


if __name__ == '__main__':
    envname = os.environ.get('envname', 'local')
    engine = get_engine(envname=envname)

    load_modules({ImportMode.STACK_UPDATER_TASK})
    update_stacks(engine=engine, envname=envname)
