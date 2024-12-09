import json
import logging

from dataall.base.api.context import Context
from dataall.base.db.exceptions import RequiredParameter
from dataall.modules.s3_datasets.services.dataset_profiling_service import DatasetProfilingService
from dataall.modules.s3_datasets.services.dataset_service import DatasetService
from dataall.modules.s3_datasets.db.dataset_models import DatasetProfilingRun

log = logging.getLogger(__name__)


def _validate_uri(uri):
    if not uri:
        raise RequiredParameter('URI')


def resolve_dataset(context, source: DatasetProfilingRun):
    if not source:
        return None
    return DatasetService.get_dataset(uri=source.datasetUri)


def start_profiling_run(context: Context, source, input: dict = None):
    _validate_uri(input.get('datasetUri'))

    return DatasetProfilingService.start_profiling_run(
        uri=input['datasetUri'], table_uri=input.get('tableUri'), glue_table_name=input.get('GlueTableName')
    )


def resolve_profiling_run_status(context: Context, source: DatasetProfilingRun):
    if not source:
        return None
    DatasetProfilingService.resolve_profiling_run_status(source.profilingRunUri)
    return source.status


def resolve_profiling_results(context: Context, source: DatasetProfilingRun):
    if not source or source.results == {}:
        return None
    else:
        return json.dumps(source.results)


def get_dataset_table_profiling_run(context: Context, source, tableUri=None):
    return DatasetProfilingService.get_dataset_table_profiling_run(uri=tableUri)


def list_table_profiling_runs(context: Context, source, tableUri=None):
    return DatasetProfilingService.list_table_profiling_runs(uri=tableUri)
