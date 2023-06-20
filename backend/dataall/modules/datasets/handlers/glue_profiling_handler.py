import logging
from botocore.exceptions import ClientError

from dataall.aws.handlers.service_handlers import Worker
from dataall.aws.handlers.sts import SessionHelper
from dataall.db import models
from dataall.modules.datasets.aws.glue_profiler_client import GlueDatasetProfilerClient
from dataall.modules.datasets.db.models import DatasetProfilingRun, Dataset
from dataall.modules.datasets.services.dataset_profiling_service import DatasetProfilingService

log = logging.getLogger(__name__)


class DatasetProfilingGlueHandler:
    """A handler for dataset profiling"""

    @staticmethod
    @Worker.handler('glue.job.profiling_run_status')
    def get_profiling_run(engine, task: models.Task):
        with engine.scoped_session() as session:
            dataset, profiling = DatasetProfilingGlueHandler._get_job_data(session, task)
            status = GlueDatasetProfilerClient(dataset).get_job_status(profiling)

            profiling.status = status
            session.commit()
            return profiling.status

    @staticmethod
    @Worker.handler('glue.job.start_profiling_run')
    def start_profiling_run(engine, task: models.Task):
        with engine.scoped_session() as session:
            dataset, profiling = DatasetProfilingGlueHandler._get_job_data(session, task)
            run_id = GlueDatasetProfilerClient(dataset).run_job(profiling)

            DatasetProfilingService.update_run(
                session,
                profilingRunUri=profiling.profilingRunUri,
                GlueJobRunId=run_id,
            )
            return run_id

    @staticmethod
    def _get_job_data(session, task):
        profiling: DatasetProfilingRun = (
            DatasetProfilingService.get_profiling_run(
                session, profilingRunUri=task.targetUri
            )
        )
        dataset: Dataset = session.query(Dataset).get(
            profiling.datasetUri
        )

        return dataset, profiling
