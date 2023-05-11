import json

from dataall.aws.handlers.service_handlers import Worker
from dataall.core.context import get_context
from dataall.core.permission_checker import has_resource_permission
from dataall.db.api import Environment, ResourcePolicy
from dataall.db.models import Task
from dataall.modules.datasets.aws.s3_profiler_client import S3ProfilerClient
from dataall.modules.datasets.db.dataset_profiling_repository import DatasetProfilingRepository
from dataall.modules.datasets.db.dataset_service import DatasetService
from dataall.modules.datasets.db.dataset_table_repository import DatasetTableRepository
from dataall.modules.datasets.services.dataset_permissions import PROFILE_DATASET_TABLE
from dataall.modules.datasets_base.db.models import DatasetProfilingRun


class DatasetProfilingService:
    @staticmethod
    @has_resource_permission(PROFILE_DATASET_TABLE)
    def start_profiling_run(uri, table_uri, glue_table_name):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            dataset = DatasetService.get_dataset_by_uri(session, uri)
            run = DatasetProfilingRepository.start_profiling(
                session=session,
                datasetUri=dataset.datasetUri,
                tableUri=table_uri,
                GlueTableName=glue_table_name,
            )

            task = Task(
                targetUri=run.profilingRunUri, action='glue.job.start_profiling_run'
            )
            session.add(task)

        Worker.process(engine=context.db_engine, task_ids=[task.taskUri])

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
    def update_profiling_run_results(run_uri, results):
        with get_context().db_engine.scoped_session() as session:
            run = DatasetProfilingRepository.update_run(
                session=session, profilingRunUri=run_uri, results=results
            )
            return run

    @staticmethod
    def list_profiling_runs(dataset_uri):
        with get_context().db_engine.scoped_session() as session:
            return DatasetProfilingRepository.list_profiling_runs(session, dataset_uri)

    @staticmethod
    def get_profiling_run(run_uri):
        with get_context().db_engine.scoped_session() as session:
            return DatasetProfilingRepository.get_profiling_run(
                session=session, profilingRunUri=run_uri
            )

    @staticmethod
    def get_last_table_profiling_run(table_uri: str):
        with get_context().db_engine.scoped_session() as session:
            run: DatasetProfilingRun = (
                DatasetProfilingRepository.get_table_last_profiling_run(
                    session=session, tableUri=table_uri
                )
            )

            if run:
                if not run.results:
                    table = DatasetTableRepository.get_dataset_table_by_uri(session, table_uri)
                    dataset = DatasetService.get_dataset_by_uri(session, table.datasetUri)
                    environment = Environment.get_environment_by_uri(session, dataset.environmentUri)
                    content = S3ProfilerClient(environment).get_profiling_results_from_s3(dataset, table, run)
                    if content:
                        results = json.loads(content)
                        run.results = results

                if not run.results:
                    run_with_results = (
                        DatasetProfilingRepository.get_table_last_profiling_run_with_results(session, table_uri)
                    )
                    if run_with_results:
                        run = run_with_results

            return run

    @staticmethod
    def list_table_profiling_runs(table_uri: str):
        with get_context().db_engine.scoped_session() as session:
            return DatasetProfilingRepository.list_table_profiling_runs(
                session=session, tableUri=table_uri, filter={}
            )
