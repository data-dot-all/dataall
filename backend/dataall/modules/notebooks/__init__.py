"""Contains the code related to SageMaker notebooks"""
import logging

from dataall.modules.loader import ImportMode

log = logging.getLogger(__name__)


class NotebookInterface:
    # Implements ModuleInterface protocol

    def initialize(self, modes):
        if ImportMode.API in modes:
            import dataall.modules.notebooks.api
        if ImportMode.CDK in modes:
            import dataall.modules.notebooks.cdk

        log.info("Sagemaker notebooks has been imported")

