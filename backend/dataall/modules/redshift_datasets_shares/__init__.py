import logging
from typing import List, Type, Set

from dataall.base.loader import ModuleInterface, ImportMode


log = logging.getLogger(__name__)


class RedshiftDatasetsSharesApiModuleInterface(ModuleInterface):
    @staticmethod
    def is_supported(modes: Set[ImportMode]) -> bool:
        return ImportMode.API in modes

    @staticmethod
    def depends_on() -> List[Type['ModuleInterface']]:
        from dataall.modules.notifications import NotificationsModuleInterface
        from dataall.modules.redshift_datasets import RedshiftDatasetApiModuleInterface
        from dataall.modules.shares_base import SharesBaseAPIModuleInterface

        return [RedshiftDatasetApiModuleInterface, NotificationsModuleInterface, SharesBaseAPIModuleInterface]

    def __init__(self):
        from dataall.core.environment.services.environment_resource_manager import EnvironmentResourceManager
        from dataall.modules.redshift_datasets_shares import api
        from dataall.modules.redshift_datasets_shares.db.redshift_share_object_repositories import (
            RedshiftShareEnvironmentResource,
        )

        from dataall.modules.shares_base.services.share_processor_manager import (
            ShareProcessorManager,
            ShareProcessorDefinition,
        )
        from dataall.modules.shares_base.services.shares_enums import ShareableType
        from dataall.modules.redshift_datasets.db.redshift_models import RedshiftTable
        from dataall.modules.redshift_datasets_shares.services.redshift_table_share_processor import (
            ProcessRedshiftShare,
        )

        EnvironmentResourceManager.register(RedshiftShareEnvironmentResource())

        ShareProcessorManager.register_processor(
            ShareProcessorDefinition(
                ShareableType.RedshiftTable, ProcessRedshiftShare, RedshiftTable, RedshiftTable.rsTableUri
            )
        )

        log.info('API of redshift dataset sharing has been imported')


class RedshiftDatasetsSharesCdkModuleInterface(ModuleInterface):
    """Implements ModuleInterface for data sharing"""

    @staticmethod
    def is_supported(modes):
        return ImportMode.CDK in modes

    def __init__(self):
        import dataall.modules.redshift_datasets_shares.cdk

        log.info('CDK module redshift_datasets_shares has been imported')


class RedshiftDatasetsSharesECSShareModuleInterface(ModuleInterface):
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

        from dataall.modules.redshift_datasets.db.redshift_models import RedshiftTable
        from dataall.modules.redshift_datasets_shares.services.redshift_table_share_processor import (
            ProcessRedshiftShare,
        )

        ShareProcessorManager.register_processor(
            ShareProcessorDefinition(
                ShareableType.RedshiftTable, ProcessRedshiftShare, RedshiftTable, RedshiftTable.rsTableUri
            )
        )

        log.info('ECS Share module redshift_datasets_shares has been imported')
