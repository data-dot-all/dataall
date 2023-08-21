"""Contains the code related to datapipelines"""
import logging
from typing import List, Type

from dataall.base.loader import ModuleInterface, ImportMode
from dataall.core.environment.services.environment_resource_manager import EnvironmentResourceManager
from dataall.modules.datapipelines.db.datapipelines_models import DataPipeline
from dataall.modules.datapipelines.db.datapipelines_repositories import DatapipelinesRepository
from dataall.modules.datapipelines.services.datapipelines_permissions import \
    GET_PIPELINE, UPDATE_PIPELINE

log = logging.getLogger(__name__)


class DatapipelinesApiModuleInterface(ModuleInterface):
    """Implements ModuleInterface for datapipelines GraphQl lambda"""

    @staticmethod
    def is_supported(modes):
        return ImportMode.API in modes

    @staticmethod
    def depends_on() -> List[Type['ModuleInterface']]:
        from dataall.modules.feed import FeedApiModuleInterface

        return [FeedApiModuleInterface]

    def __init__(self):
        # these imports are placed inside the method because they are only related to GraphQL api.
        from dataall.core.stacks.db.target_type_repositories import TargetType
        from dataall.modules.feed.api.registry import FeedRegistry, FeedDefinition

        import dataall.modules.datapipelines.api
        FeedRegistry.register(FeedDefinition("DataPipeline", DataPipeline))

        TargetType("pipeline", GET_PIPELINE, UPDATE_PIPELINE)

        EnvironmentResourceManager.register(DatapipelinesRepository())

        log.info("API of datapipelines has been imported")


class DatapipelinesAsyncHandlersModuleInterface(ModuleInterface):
    """Implements ModuleInterface for datapipelines async lambda"""

    @staticmethod
    def is_supported(modes: List[ImportMode]):
        return ImportMode.HANDLERS in modes

    def __init__(self):
        import dataall.modules.datapipelines.handlers
        log.info("Datapipelines handlers have been imported")


class DatapipelinesCdkModuleInterface(ModuleInterface):
    """Loads datapipelines cdk stacks """

    @staticmethod
    def is_supported(modes: List[ImportMode]):
        return ImportMode.CDK in modes

    def __init__(self):
        import dataall.modules.datapipelines.cdk
        from dataall.base.cdkproxy.cdk_cli_wrapper import _CDK_CLI_WRAPPER_EXTENSIONS
        from dataall.modules.datapipelines.cdk.datapipelines_cdk_cli_wrapper_extension import \
            DatapipelinesCDKCliWrapperExtension

        _CDK_CLI_WRAPPER_EXTENSIONS['cdkpipeline'] = DatapipelinesCDKCliWrapperExtension()

        log.info("Datapipelines stacks have been imported")
