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
        from dataall.modules.shares_base import SharesBaseAPIModuleInterface

        return [DatasetApiModuleInterface, NotificationsModuleInterface, SharesBaseAPIModuleInterface]

    def __init__(self):
        from dataall.core.environment.services.environment_resource_manager import EnvironmentResourceManager
        from dataall.modules.s3_datasets_shares import api
        from dataall.modules.s3_datasets_shares.services.s3_share_managed_policy_service import S3SharePolicyService
        from dataall.modules.s3_datasets.services.dataset_service import DatasetService
        from dataall.modules.datasets_base.services.datasets_enums import DatasetTypes
        from dataall.modules.datasets_base.services.dataset_list_service import DatasetListService
        from dataall.modules.s3_datasets_shares.services.s3_share_dataset_service import S3ShareDatasetService
        from dataall.modules.s3_datasets_shares.db.s3_share_object_repositories import S3ShareEnvironmentResource
        from dataall.modules.shares_base.services.share_processor_manager import (
            ShareProcessorManager,
            ShareProcessorDefinition,
        )
        from dataall.modules.shares_base.services.shares_enums import ShareableType
        from dataall.modules.shares_base.services.share_object_service import ShareObjectService
        from dataall.modules.s3_datasets.db.dataset_models import DatasetTable, DatasetBucket, DatasetStorageLocation
        from dataall.modules.s3_datasets_shares.services.s3_share_validator import S3ShareValidator

        from dataall.modules.s3_datasets_shares.services.share_processors.glue_table_share_processor import (
            ProcessLakeFormationShare,
        )
        from dataall.modules.s3_datasets_shares.services.share_processors.s3_bucket_share_processor import (
            ProcessS3BucketShare,
        )
        from dataall.modules.s3_datasets_shares.services.share_processors.s3_access_point_share_processor import (
            ProcessS3AccessPointShare,
        )

        EnvironmentResourceManager.register(S3ShareEnvironmentResource())
        DatasetService.register(S3ShareDatasetService())
        DatasetListService.register(S3ShareDatasetService())

        ShareProcessorManager.register_processor(
            ShareProcessorDefinition(
                ShareableType.Table, ProcessLakeFormationShare, DatasetTable, DatasetTable.tableUri
            )
        )
        ShareProcessorManager.register_processor(
            ShareProcessorDefinition(
                ShareableType.S3Bucket, ProcessS3BucketShare, DatasetBucket, DatasetBucket.bucketUri
            )
        )
        ShareProcessorManager.register_processor(
            ShareProcessorDefinition(
                ShareableType.StorageLocation,
                ProcessS3AccessPointShare,
                DatasetStorageLocation,
                DatasetStorageLocation.locationUri,
            )
        )

        ShareObjectService.register_validator(dataset_type=DatasetTypes.S3, validator=S3ShareValidator)

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
        from dataall.modules.shares_base import SharesBaseAsyncHandlerModuleInterface

        return [
            DatasetAsyncHandlersModuleInterface,
            NotificationsModuleInterface,
            SharesBaseAsyncHandlerModuleInterface,
        ]

    def __init__(self):
        log.info('s3_datasets_shares handlers have been imported')


class S3DatasetsSharesCdkModuleInterface(ModuleInterface):
    """Implements ModuleInterface for data sharing"""

    @staticmethod
    def is_supported(modes):
        return ImportMode.CDK in modes

    def __init__(self):
        import dataall.modules.s3_datasets_shares.cdk
        from dataall.modules.s3_datasets_shares.services.s3_share_managed_policy_service import S3SharePolicyService

        log.info('CDK module s3_datasets_shares has been imported')


class S3DatasetsSharesECSShareModuleInterface(ModuleInterface):
    """Implements ModuleInterface for data sharing"""

    @staticmethod
    def is_supported(modes):
        return ImportMode.SHARES_TASK in modes

    @staticmethod
    def depends_on() -> List[Type['ModuleInterface']]:
        from dataall.modules.shares_base import SharesBaseECSTaskModuleInterface
        from dataall.modules.notifications import NotificationsModuleInterface

        return [SharesBaseECSTaskModuleInterface, NotificationsModuleInterface]

    def __init__(self):
        from dataall.modules.shares_base.services.share_processor_manager import (
            ShareProcessorManager,
            ShareProcessorDefinition,
        )
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

        ShareProcessorManager.register_processor(
            ShareProcessorDefinition(
                ShareableType.Table, ProcessLakeFormationShare, DatasetTable, DatasetTable.tableUri
            )
        )
        ShareProcessorManager.register_processor(
            ShareProcessorDefinition(
                ShareableType.S3Bucket, ProcessS3BucketShare, DatasetBucket, DatasetBucket.bucketUri
            )
        )
        ShareProcessorManager.register_processor(
            ShareProcessorDefinition(
                ShareableType.StorageLocation,
                ProcessS3AccessPointShare,
                DatasetStorageLocation,
                DatasetStorageLocation.locationUri,
            )
        )

        log.info('ECS Share module s3_datasets_shares has been imported')
