from dataall.base.context import get_context
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.modules.s3_datasets.services.dataset_permissions import CREATE_DATASET_TABLE_QUALITY_RULE
from dataall.modules.s3_datasets.db.dataset_table_quality_repository import DatasetTableQualityRepository

class DatasetTableQualityService:

    @staticmethod
    def list_glue_quality_rules():
        context = get_context()
        with context.db_engine.scoped_session() as session:
            return DatasetTableQualityRepository.list_glue_quality_rules(session)

    @staticmethod
    @ResourcePolicyService.has_resource_permission(CREATE_DATASET_TABLE_QUALITY_RULE)
    def list_table_data_quality_rules(uri: str):
        pass

