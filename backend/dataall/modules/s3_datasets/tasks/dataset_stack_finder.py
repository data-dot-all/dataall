import logging
from typing import List

from dataall.core.environment.tasks.env_stack_finder import StackFinder
from dataall.modules.datasets_base.services.datasets_enums import DatasetType
from dataall.modules.datasets_base.db.dataset_repositories import DatasetListRepository
from dataall.modules.s3_datasets.db.dataset_models import S3Dataset

log = logging.getLogger(__name__)


class DatasetStackFinder(StackFinder):
    """
    Dataset stack finder. Looks for datasets stack to update
    Register automatically itself when StackFinder instance is created
    """

    def find_stack_uris(self, session) -> List[str]:
        all_datasets: [S3Dataset] = DatasetListRepository.list_all_active_datasets(session=session, dataset_type=DatasetType.S3)
        log.info(f'Found {len(all_datasets)} datasets')
        return [dataset.datasetUri for dataset in all_datasets]
