import logging
import os
import sys
import time

from .. import db
from ..db import models
from ..aws.handlers.ecs import Ecs
from ..db import get_engine
from ..utils import Parameter

root = logging.getLogger()
root.setLevel(logging.INFO)
if not root.hasHandlers():
    root.addHandler(logging.StreamHandler(sys.stdout))
log = logging.getLogger(__name__)


def update_stacks(engine, envname):
    with engine.scoped_session() as session:

        all_datasets: [models.Dataset] = db.api.Dataset.list_all_active_datasets(session)
        all_environments: [models.Environment] = db.api.Environment.list_all_active_environments(session)

        log.info(f'Found {len(all_environments)} environments, triggering update stack tasks...')
        environment: models.Environment
        for environment in all_environments:
            update_stack(session, envname, environment.environmentUri)

        environments_being_updated = [True]
        retries = 1
        while any(environments_being_updated):
            if retries > 1:
                log.info("Update for environments is not complete, waiting for 30 seconds...")
                time.sleep(30)
            retries = retries + 1
            environments_being_updated = []
            for environment in all_environments:
                env_running = check_stack(session, envname, environment.environmentUri)
                log.info(f"Update for {environment.environmentUri} is not complete" if env_running else f"Update for {environment.environmentUri} is COMPLETE")
                environments_being_updated.append(env_running)
            if retries > 60:
                log.info("Maximum number of retries exceeded (30mins), continuing task...")
                break

        log.info("Update for all environments COMPLETE or maximum number of retries exceeded")
        log.info(f'Found {len(all_datasets)} datasets, triggering update stack tasks...')
        dataset: models.Dataset
        for dataset in all_datasets:
            update_stack(session, envname, dataset.datasetUri)

        return all_environments, all_datasets


def check_stack(session, envname, target_uri):
    stack: models.Stack = db.api.Stack.get_stack_by_target_uri(
        session, target_uri=target_uri
    )
    log.info(f"Checking task for stack {stack.name}//{stack.stackUri}")
    cluster_name = Parameter().get_parameter(env=envname, path='ecs/cluster/name')
    return Ecs.is_task_running(cluster_name=cluster_name, started_by=f'awsworker-{stack.stackUri}')


def update_stack(session, envname, target_uri):
    stack: models.Stack = db.api.Stack.get_stack_by_target_uri(
        session, target_uri=target_uri
    )
    cluster_name = Parameter().get_parameter(env=envname, path='ecs/cluster/name')
    if not Ecs.is_task_running(cluster_name=cluster_name, started_by=f'awsworker-{stack.stackUri}'):
        log.info(f"Updating stack {stack.name}//{stack.stackUri}")
        stack.EcsTaskArn = Ecs.run_cdkproxy_task(stack_uri=stack.stackUri)
    else:
        log.info(
            f'Stack update is already running... Skipping stack {stack.name}//{stack.stackUri}'
        )


if __name__ == '__main__':
    envname = os.environ.get('envname', 'local')
    engine = get_engine(envname=envname)
    update_stacks(engine=engine, envname=envname)
