from dataall.core.group.services.group_resource_manager import GroupResource
from dataall.modules.datasets_base.db.dataset_repository import DatasetRepository


class DatasetGroupResource(GroupResource):
    def count_resources(self, session, environment_uri, group_uri) -> int:
        return DatasetRepository.count_group_datasets(session, environment_uri, group_uri)

