import logging
import os

from dataall.core.tasks.service_handlers import Worker
from dataall.core.stacks.aws.ecs import Ecs
from dataall.core.tasks.db.task_models import Task
from dataall.modules.catalog.tasks.catalog_indexer_task import CatalogIndexerTask

log = logging.getLogger(__name__)


class EcsCatalogIndexHandler:
    @staticmethod
    @Worker.handler(path='ecs.reindex.catalog')
    def run_ecs_reindex_catalog_task(engine, task: Task):
        envname = os.environ.get('envname', 'local')
        if envname in ['local', 'dkrcompose']:
            CatalogIndexerTask.index_objects(engine, str(task.payload.get('with_deletes', False)))
        else:
            ecs_task_arn = Ecs.run_ecs_task(
                task_definition_param='ecs/task_def_arn/catalog_indexer',
                container_name_param='ecs/container/catalog_indexer',
                context=[
                    {'name': 'with_deletes', 'value': str(task.payload.get('with_deletes', False))},
                ],
            )
            return {'task_arn': ecs_task_arn}
