import json

from dataall.core.tasks.service_handlers import Worker
from dataall.base.context import get_context
from dataall.core.environment.db.models import Environment
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.permissions.permission_checker import has_resource_permission
from dataall.core.tasks.db.task_models import Task
from dataall.db.exceptions import ObjectNotFound
from dataall.modules.datasets.aws.glue_profiler_client import GlueDatasetProfilerClient
from dataall.modules.datasets.aws.s3_profiler_client import S3ProfilerClient
from dataall.modules.datasets.db.dataset_profiling_repository import DatasetProfilingRepository
from dataall.modules.datasets.db.dataset_table_repository import DatasetTableRepository
from dataall.modules.datasets.services.dataset_permissions import PROFILE_DATASET_TABLE, GET_DATASET
from dataall.modules.datasets_base.db.dataset_repository import DatasetRepository
from dataall.modules.datasets_base.db.models import DatasetProfilingRun, DatasetTable
from dataall.modules.datasets_base.services.permissions import GET_DATASET_TABLE


class DatasetProfilingService:
    @staticmethod
    @has_resource_permission(PROFILE_DATASET_TABLE)
    def start_profiling_run(uri, table_uri, glue_table_name):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            dataset = DatasetRepository.get_dataset_by_uri(session, uri)

            if table_uri and not glue_table_name:
                table: DatasetTable = DatasetTableRepository.get_dataset_table_by_uri(session, table_uri)
                if not table:
                    raise ObjectNotFound('DatasetTable', table_uri)
                glue_table_name = table.GlueTableName

            environment: Environment = EnvironmentService.get_environment_by_uri(session, dataset.environmentUri)
            if not environment:
                raise ObjectNotFound('Environment', dataset.environmentUri)

            run = DatasetProfilingRepository.save_profiling(
                session=session,
                dataset=dataset,
                env=environment,
                glue_table_name=glue_table_name,
            )

            run_id = GlueDatasetProfilerClient(dataset).run_job(run)

            DatasetProfilingRepository.update_run(
                session,
                run_uri=run.profilingRunUri,
                glue_job_run_id=run_id,
            )

        return run

    @staticmethod
    def queue_profiling_run(run_uri):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            task = Task(
                targetUri=run_uri, action='glue.job.profiling_run_status'
            )
            session.add(task)
        Worker.queue(engine=context.db_engine, task_ids=[task.taskUri])

    @staticmethod
    @has_resource_permission(GET_DATASET)
    def list_profiling_runs(uri):
        with get_context().db_engine.scoped_session() as session:
            return DatasetProfilingRepository.list_profiling_runs(session, uri)

    @staticmethod
    @has_resource_permission(GET_DATASET_TABLE)
    def get_last_table_profiling_run(uri: str):
        with get_context().db_engine.scoped_session() as session:
            run: DatasetProfilingRun = (
                DatasetProfilingRepository.get_table_last_profiling_run(session, uri)
            )

            if run:
                if not run.results:
                    table = DatasetTableRepository.get_dataset_table_by_uri(session, uri)
                    dataset = DatasetRepository.get_dataset_by_uri(session, table.datasetUri)
                    environment = EnvironmentService.get_environment_by_uri(session, dataset.environmentUri)
                    content = S3ProfilerClient(environment).get_profiling_results_from_s3(dataset, table, run)
                    if content:
                        results = json.loads(content)
                        run.results = results

                if not run.results:
                    run_with_results = (
                        DatasetProfilingRepository.get_table_last_profiling_run_with_results(session, uri)
                    )
                    if run_with_results:
                        run = run_with_results

            return run

    @staticmethod
    @has_resource_permission(GET_DATASET_TABLE)
    def list_table_profiling_runs(uri: str):
        with get_context().db_engine.scoped_session() as session:
            return DatasetProfilingRepository.list_table_profiling_runs(session, uri)
