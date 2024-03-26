import logging
from typing import List, Type, Set

from dataall.core.environment.services.environment_resource_manager import EnvironmentResourceManager
from dataall.modules.s3_dataset_sharing.db.share_object_repositories import ShareEnvironmentResource
from dataall.base.loader import ModuleInterface, ImportMode


log = logging.getLogger(__name__)


class S3SharingApiModuleInterface(ModuleInterface):
    @staticmethod
    def is_supported(modes: Set[ImportMode]) -> bool:
        return ImportMode.API in modes

    @staticmethod
    def depends_on() -> List[Type['ModuleInterface']]:
        from dataall.modules.notifications import NotificationsModuleInterface
        from dataall.modules.s3_datasets import S3DatasetApiModuleInterface

        return [S3DatasetApiModuleInterface, NotificationsModuleInterface]

    def __init__(self):
        from dataall.modules.s3_dataset_sharing import api
        from dataall.modules.s3_dataset_sharing.services.managed_share_policy_service import SharePolicyService

        EnvironmentResourceManager.register(ShareEnvironmentResource())
        log.info('API of dataset sharing has been imported')


class S3SharingAsyncHandlersModuleInterface(ModuleInterface):
    """Implements ModuleInterface for dataset async lambda"""

    @staticmethod
    def is_supported(modes: List[ImportMode]):
        return ImportMode.HANDLERS in modes

    @staticmethod
    def depends_on() -> List[Type['ModuleInterface']]:
        from dataall.modules.notifications import NotificationsModuleInterface
        from dataall.modules.s3_datasets import S3DatasetAsyncHandlersModuleInterface

        return [S3DatasetAsyncHandlersModuleInterface, NotificationsModuleInterface]

    def __init__(self):
        import dataall.modules.s3_dataset_sharing.handlers

        log.info('Sharing handlers have been imported')


class S3DataSharingCdkModuleInterface(ModuleInterface):
    """Implements ModuleInterface for data sharing"""

    @staticmethod
    def is_supported(modes):
        return ImportMode.CDK in modes

    def __init__(self):
        import dataall.modules.s3_dataset_sharing.cdk
        from dataall.modules.s3_dataset_sharing.services.managed_share_policy_service import SharePolicyService

        log.info('CDK module data_sharing has been imported')
