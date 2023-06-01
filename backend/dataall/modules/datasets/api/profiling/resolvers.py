import json
import logging

from dataall.api.context import Context
from dataall.db.exceptions import RequiredParameter
from dataall.modules.datasets.services.dataset_profiling_service import DatasetProfilingService
from dataall.modules.datasets.services.dataset_service import DatasetService
from dataall.modules.datasets_base.db.models import DatasetProfilingRun

log = logging.getLogger(__name__)


def resolve_dataset(context, source: DatasetProfilingRun):
    if not source:
        return None
    return DatasetService.get_dataset(uri=source.datasetUri)


def start_profiling_run(context: Context, source, input: dict = None):
    if 'datasetUri' not in input:
        raise RequiredParameter('datasetUri')

    return DatasetProfilingService.start_profiling_run(
        uri=input['datasetUri'],
        table_uri=input.get('tableUri'),
        glue_table_name=input.get('GlueTableName')
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

def list_profiling_runs(context: Context, source, datasetUri=None):
    return DatasetProfilingService.list_profiling_runs(datasetUri)


def get_last_table_profiling_run(context: Context, source, tableUri=None):
    return DatasetProfilingService.get_last_table_profiling_run(tableUri)


def list_table_profiling_runs(context: Context, source, tableUri=None):
    return DatasetProfilingService.list_table_profiling_runs(tableUri)
