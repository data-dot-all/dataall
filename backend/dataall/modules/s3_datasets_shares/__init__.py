import logging
from typing import List, Type, Set

from dataall.base.loader import ModuleInterface, ImportMode


log = logging.getLogger(__name__)


class S3DatasetsSharesApiModuleInterface(ModuleInterface):
    @staticmethod
    def is_supported(modes: Set[ImportMode]) -> bool:
        return ImportMode.API in modes

    @staticmethod
    def depends_on() -> List[Type['ModuleInterface']]:
        from dataall.modules.notifications import NotificationsModuleInterface
        from dataall.modules.s3_datasets import DatasetApiModuleInterface
        from dataall.modules.shares_base import SharesBaseModuleInterface

        return [DatasetApiModuleInterface, NotificationsModuleInterface, SharesBaseModuleInterface]

    def __init__(self):
        from dataall.core.environment.services.environment_resource_manager import EnvironmentResourceManager
        from dataall.modules.s3_datasets_shares import api
        from dataall.modules.s3_datasets_shares.services.managed_share_policy_service import SharePolicyService
        from dataall.modules.s3_datasets.services.dataset_service import DatasetService
        from dataall.modules.datasets_base.services.dataset_list_service import DatasetListService
        from dataall.modules.s3_datasets_shares.services.dataset_sharing_service import DatasetSharingService
        from dataall.modules.s3_datasets_shares.db.share_object_repositories import ShareEnvironmentResource

        EnvironmentResourceManager.register(ShareEnvironmentResource())
        DatasetService.register(DatasetSharingService())
        DatasetListService.register(DatasetSharingService())
        log.info('API of dataset sharing has been imported')


class S3DatasetsSharesAsyncHandlersModuleInterface(ModuleInterface):
    """Implements ModuleInterface for dataset async lambda"""

    @staticmethod
    def is_supported(modes: List[ImportMode]):
        return ImportMode.HANDLERS in modes

    @staticmethod
    def depends_on() -> List[Type['ModuleInterface']]:
        from dataall.modules.notifications import NotificationsModuleInterface
        from dataall.modules.s3_datasets import DatasetAsyncHandlersModuleInterface
        from dataall.modules.shares_base import SharesBaseAsyncModuleInterface

        return [DatasetAsyncHandlersModuleInterface, NotificationsModuleInterface, SharesBaseAsyncModuleInterface]

    def __init__(self):
        log.info('S3 Sharing handlers have been imported')


class S3DatasetsSharesCdkModuleInterface(ModuleInterface):
    """Implements ModuleInterface for data sharing"""

    @staticmethod
    def is_supported(modes):
        return ImportMode.CDK in modes

    def __init__(self):
        import dataall.modules.s3_datasets_shares.cdk
        from dataall.modules.s3_datasets_shares.services.managed_share_policy_service import SharePolicyService

        log.info('CDK module data_sharing has been imported')


class S3DatasetsSharesECSShareModuleInterface(ModuleInterface):
    """Implements ModuleInterface for data sharing"""

    @staticmethod
    def is_supported(modes):
        return ImportMode.SHARES_TASK in modes

    def __init__(self):
        from dataall.modules.shares_base.services.sharing_service import SharingService, SharingProcessorDefinition
        from dataall.modules.shares_base.services.shares_enums import ShareableType
        from dataall.modules.s3_datasets.db.dataset_models import DatasetTable, DatasetBucket, DatasetStorageLocation
        from dataall.modules.s3_datasets_shares.services.share_processors.glue_table_share_processor import (
            ProcessLakeFormationShare,
        )
        from dataall.modules.s3_datasets_shares.services.share_processors.s3_bucket_share_processor import (
            ProcessS3BucketShare,
        )
        from dataall.modules.s3_datasets_shares.services.share_processors.s3_access_point_share_processor import (
            ProcessS3AccessPointShare,
        )

        SharingService.register_processor(
            SharingProcessorDefinition(
                ShareableType.Table, ProcessLakeFormationShare, DatasetTable, DatasetTable.tableUri
            )
        )
        SharingService.register_processor(
            SharingProcessorDefinition(
                ShareableType.S3Bucket, ProcessS3BucketShare, DatasetBucket, DatasetBucket.bucketUri
            )
        )
        SharingService.register_processor(
            SharingProcessorDefinition(
                ShareableType.StorageLocation,
                ProcessS3AccessPointShare,
                DatasetStorageLocation,
                DatasetStorageLocation.locationUri,
            )
        )

        log.info('ECS Share module s3_data_sharing has been imported')
