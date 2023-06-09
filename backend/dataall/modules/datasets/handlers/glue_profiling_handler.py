import logging

from dataall.aws.handlers.service_handlers import Worker
from dataall.db import models
from dataall.modules.datasets.aws.glue_profiler_client import GlueDatasetProfilerClient
from dataall.modules.datasets_base.db.dataset_repository import DatasetRepository
from dataall.modules.datasets_base.db.models import DatasetProfilingRun, Dataset
from dataall.modules.datasets.db.dataset_profiling_repository import DatasetProfilingRepository

log = logging.getLogger(__name__)


class DatasetProfilingGlueHandler:
    """A handler for dataset profiling"""

    @staticmethod
    @Worker.handler('glue.job.profiling_run_status')
    def get_profiling_run(engine, task: models.Task):
        with engine.scoped_session() as session:
            profiling: DatasetProfilingRun = (
                DatasetProfilingRepository.get_profiling_run(
                    session, profiling_run_uri=task.targetUri
                )
            )
            dataset: Dataset = DatasetRepository.get_dataset_by_uri(session, profiling.datasetUri)
            status = GlueDatasetProfilerClient(dataset).get_job_status(profiling)

            profiling.status = status
            session.commit()
            return profiling.status
