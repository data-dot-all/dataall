import logging
import os
import sys

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

        all_datasets: [models.Dataset] = db.api.Dataset.list_all_active_datasets(
            session
        )
        all_environments: [
            models.Environment
        ] = db.api.Environment.list_all_active_environments(session)
        log.info(f'Found {len(all_environments)} environments')
        environment: models.Environment
        for environment in all_environments:
            update_stack(session, envname, environment.environmentUri)

        log.info(f'Found {len(all_datasets)} datasets')
        dataset: models.Dataset
        for dataset in all_datasets:
            update_stack(session, envname, dataset.datasetUri)

        return all_environments, all_datasets


def update_stack(session, envname, target_uri):
    stack: models.Stack = db.api.Stack.get_stack_by_target_uri(
        session, target_uri=target_uri
    )
    cluster_name = Parameter().get_parameter(env=envname, path='ecs/cluster/name')
    if not Ecs.is_task_running(cluster_name, f'awsworker-{stack.stackUri}'):
        stack.EcsTaskArn = Ecs.run_cdkproxy_task(stack.stackUri)
    else:
        log.info(
            f'Stack update is already running... Skipping stack {stack.name}//{stack.stackUri}'
        )


if __name__ == '__main__':
    envname = os.environ.get('envname', 'local')
    engine = get_engine(envname=envname)
    update_stacks(engine=engine, envname=envname)
