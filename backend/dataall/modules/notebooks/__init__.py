"""Contains the code related to SageMaker notebooks"""
import logging

from dataall.db.api import TargetType
from dataall.modules.loader import ImportMode
from dataall.modules.notebooks.db.repositories import NotebookRepository

log = logging.getLogger(__name__)


class NotebookInterface:
    """Implements ModuleInterface protocol"""

    def initialize(self, modes):
        if ImportMode.API in modes:
            import dataall.modules.notebooks.api

            from dataall.modules.notebooks.services.permissions import GET_NOTEBOOK, UPDATE_NOTEBOOK
            TargetType("notebook", GET_NOTEBOOK, UPDATE_NOTEBOOK)

        if ImportMode.CDK in modes:
            import dataall.modules.notebooks.cdk

        log.info("Sagemaker notebooks has been imported")

