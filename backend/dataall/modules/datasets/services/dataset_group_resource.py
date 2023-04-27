from dataall.core.group.services.group_resource_manager import GroupResource, GroupResourceManager
from dataall.modules.datasets.db.dataset_repository import DatasetRepository


class DatasetGroupResource(GroupResource):
    def count_resources(self, session, environment_uri, group_uri) -> int:
        return DatasetRepository.count_group_datasets(session, environment_uri, group_uri)


GroupResourceManager.register(DatasetGroupResource())

