import json

from dataall.base.feature_toggle_checker import is_feature_enabled
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyService
from dataall.core.tasks.service_handlers import Worker
from dataall.base.context import get_context
from dataall.base.db import exceptions
from dataall.core.environment.db.environment_models import Environment
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.tasks.db.task_models import Task
from dataall.base.db.exceptions import ObjectNotFound
from dataall.modules.s3_datasets.aws.glue_profiler_client import GlueDatasetProfilerClient
from dataall.modules.s3_datasets.aws.s3_profiler_client import S3ProfilerClient
from dataall.modules.s3_datasets.db.dataset_profiling_repositories import DatasetProfilingRepository
from dataall.modules.s3_datasets.db.dataset_table_repositories import DatasetTableRepository
from dataall.modules.s3_datasets.services.dataset_permissions import PROFILE_DATASET_TABLE, GET_DATASET, MANAGE_DATASETS
from dataall.modules.s3_datasets.db.dataset_repositories import DatasetRepository
from dataall.modules.datasets_base.services.datasets_enums import ConfidentialityClassification
from dataall.modules.s3_datasets.db.dataset_models import DatasetProfilingRun, DatasetTable
from dataall.modules.s3_datasets.services.dataset_permissions import PREVIEW_DATASET_TABLE


class DatasetProfilingService:
    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_DATASETS)
    @ResourcePolicyService.has_resource_permission(PROFILE_DATASET_TABLE)
    @is_feature_enabled('modules.s3_datasets.features.metrics_data')
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
    @is_feature_enabled('modules.s3_datasets.features.metrics_data')
    def resolve_profiling_run_status(run_uri):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            task = Task(targetUri=run_uri, action='glue.job.profiling_run_status')
            session.add(task)
        Worker.queue(engine=context.db_engine, task_ids=[task.taskUri])

    @classmethod
    @is_feature_enabled('modules.s3_datasets.features.metrics_data')
    def get_dataset_table_profiling_run(cls, uri: str):
        with get_context().db_engine.scoped_session() as session:
            cls._check_preview_permissions_if_needed(session, table_uri=uri)
            run: DatasetProfilingRun = DatasetProfilingRepository.get_table_last_profiling_run(session, uri)

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
                    run_with_results = DatasetProfilingRepository.get_table_last_profiling_run_with_results(
                        session, uri
                    )
                    if run_with_results:
                        run = run_with_results

            return run

    @classmethod
    @is_feature_enabled('modules.s3_datasets.features.metrics_data')
    def list_table_profiling_runs(cls, uri: str):
        with get_context().db_engine.scoped_session() as session:
            cls._check_preview_permissions_if_needed(session=session, table_uri=uri)
            return DatasetProfilingRepository.list_table_profiling_runs(session, uri)

    @staticmethod
    def _check_preview_permissions_if_needed(session, table_uri):
        context = get_context()
        table: DatasetTable = DatasetTableRepository.get_dataset_table_by_uri(session, table_uri)
        dataset = DatasetRepository.get_dataset_by_uri(session, table.datasetUri)
        if (
            ConfidentialityClassification.get_confidentiality_level(dataset.confidentiality)
            != ConfidentialityClassification.Unclassified.value
        ) and (dataset.SamlAdminGroupName not in context.groups and dataset.stewards not in context.groups):
            raise exceptions.UnauthorizedOperation(
                action='GET_TABLE_PROFILING_METRICS',
                message='User is not authorized to view Profiling Metrics for Confidential datasets',
            )
        return True
