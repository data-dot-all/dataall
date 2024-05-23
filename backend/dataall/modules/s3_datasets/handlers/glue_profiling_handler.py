import logging

from dataall.core.tasks.service_handlers import Worker
from dataall.core.tasks.db.task_models import Task
from dataall.modules.s3_datasets.aws.glue_profiler_client import GlueDatasetProfilerClient
from dataall.modules.s3_datasets.db.dataset_profiling_repositories import DatasetProfilingRepository
from dataall.modules.s3_datasets.db.dataset_repositories import DatasetRepository
from dataall.modules.s3_datasets.db.dataset_models import DatasetProfilingRun, S3Dataset

log = logging.getLogger(__name__)


class DatasetProfilingGlueHandler:
    """A handler for dataset profiling"""

    @staticmethod
    @Worker.handler('glue.job.profiling_run_status')
    def get_profiling_run(engine, task: Task):
        with engine.scoped_session() as session:
            profiling: DatasetProfilingRun = DatasetProfilingRepository.get_profiling_run(
                session, profiling_run_uri=task.targetUri
            )
            dataset: S3Dataset = DatasetRepository.get_dataset_by_uri(session, profiling.datasetUri)
            status = GlueDatasetProfilerClient(dataset).get_job_status(profiling)

            profiling.status = status
            session.commit()
            return {'profiling_status': profiling.status}
