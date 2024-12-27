"""Contains the code related to datapipelines"""

import logging
from typing import List, Type

from dataall.base.loader import ModuleInterface, ImportMode

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
        from dataall.core.environment.services.environment_resource_manager import EnvironmentResourceManager
        from dataall.core.stacks.db.target_type_repositories import TargetType
        from dataall.modules.feed.api.registry import FeedRegistry, FeedDefinition
        from dataall.modules.datapipelines.db.datapipelines_models import DataPipeline
        from dataall.modules.datapipelines.db.datapipelines_repositories import DatapipelinesRepository
        from dataall.modules.datapipelines.services.datapipelines_permissions import (
            GET_PIPELINE,
            UPDATE_PIPELINE,
            MANAGE_PIPELINES,
        )
        import dataall.modules.datapipelines.api

        FeedRegistry.register(FeedDefinition('DataPipeline', DataPipeline, GET_PIPELINE))

        TargetType('pipeline', GET_PIPELINE, UPDATE_PIPELINE, MANAGE_PIPELINES)
        TargetType('cdkpipeline', GET_PIPELINE, UPDATE_PIPELINE, MANAGE_PIPELINES)

        EnvironmentResourceManager.register(DatapipelinesRepository())

        log.info('API of datapipelines has been imported')


class DatapipelinesAsyncHandlersModuleInterface(ModuleInterface):
    """Implements ModuleInterface for datapipelines async lambda"""

    @staticmethod
    def is_supported(modes: List[ImportMode]):
        return ImportMode.HANDLERS in modes

    def __init__(self):
        import dataall.modules.datapipelines.handlers

        log.info('Datapipelines handlers have been imported')


class DatapipelinesCdkModuleInterface(ModuleInterface):
    """Loads datapipelines cdk stacks"""

    @staticmethod
    def is_supported(modes: List[ImportMode]):
        # return True if CDK in modes
        return ImportMode.CDK in modes

    def __init__(self):
        from dataall.modules.datapipelines.cdk.datapipelines_pipeline import PipelineStack
        from dataall.modules.datapipelines.cdk.env_role_datapipelines_stepfunctions_policy import StepFunctions
        from dataall.modules.datapipelines.cdk.env_role_datapipelines_lambda_policy import Lambda
        from dataall.modules.datapipelines.cdk.env_role_datapipelines_cicd_policy import AwsCICD
        from dataall.modules.datapipelines.cdk.pivot_role_datapipelines_policy import PipelinesPivotRole

        log.info('Datapipelines stacks have been imported')


class DatapipelinesCdkCLIExtensionModuleInterface(ModuleInterface):
    """Loads datapipelines cdk CLI extension - for cdkpipelines"""

    @staticmethod
    def is_supported(modes: List[ImportMode]):
        # return True if CDK_CLI extension in modes
        return ImportMode.CDK_CLI_EXTENSION in modes

    def __init__(self):
        from dataall.base.cdkproxy.cdk_cli_wrapper import _CDK_CLI_WRAPPER_EXTENSIONS
        from dataall.modules.datapipelines.cdk import datapipelines_cdk_pipeline
        from dataall.modules.datapipelines.cdk.datapipelines_cdk_cli_wrapper_extension import (
            DatapipelinesCDKCliWrapperExtension,
        )

        _CDK_CLI_WRAPPER_EXTENSIONS['cdkpipeline'] = DatapipelinesCDKCliWrapperExtension()

        log.info('Datapipelines cdkpipeline stack has been imported as CDK_CLI_WRAPPER_EXTENSION')
