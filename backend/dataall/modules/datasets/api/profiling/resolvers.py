import json
import logging

from dataall.api.context import Context
from dataall.aws.handlers.service_handlers import Worker
from dataall.aws.handlers.sts import SessionHelper
from dataall.db import api, models
from dataall.db.api import ResourcePolicy
from dataall.modules.datasets.db.dataset_service import DatasetService
from dataall.modules.datasets.db.dataset_table_repository import DatasetTableRepository
from dataall.modules.datasets.db.dataset_profiling_repository import DatasetProfilingRepository
from dataall.modules.datasets.services.dataset_profiling_service import DatasetProfilingService
from dataall.modules.datasets_base.db.models import DatasetProfilingRun
from dataall.modules.datasets.services.dataset_permissions import PROFILE_DATASET_TABLE

log = logging.getLogger(__name__)


def resolve_dataset(context, source: DatasetProfilingRun):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        return DatasetService.get_dataset_by_uri(
            session=session, dataset_uri=source.datasetUri
        )


def start_profiling_run(context: Context, source, input: dict = None):
    return DatasetProfilingService.start_profiling_run(
        uri=input['datasetUri'],
        table_uri=input['table_uri'],
        glue_table_name=input['GlueTableName']
    )


def get_profiling_run_status(context: Context, source: DatasetProfilingRun):
    if not source:
        return None
    DatasetProfilingService.queue_profiling_run(source.profilingRunUri)
    return source.status


def get_profiling_results(context: Context, source: DatasetProfilingRun):
    if not source or source.results == {}:
        return None
    else:
        return json.dumps(source.results)


def update_profiling_run_results(context: Context, source, profilingRunUri, results):
    return DatasetProfilingService.update_profiling_run_results(profilingRunUri, results)


def list_profiling_runs(context: Context, source, datasetUri=None):
    return DatasetProfilingService.list_profiling_runs(datasetUri)


def get_profiling_run(context: Context, source, profilingRunUri=None):
    return DatasetProfilingService.get_profiling_run(profilingRunUri)


def get_last_table_profiling_run(context: Context, source, tableUri=None):
    return DatasetProfilingService.get_last_table_profiling_run(tableUri)


def list_table_profiling_runs(context: Context, source, tableUri=None):
    return DatasetProfilingService.list_table_profiling_runs(tableUri)
