"""Contains the code related to SageMaker notebooks"""
import logging

from dataall.modules.loader import ImportMode
from dataall.modules.notebooks.db.repositories import NotebookRepository

log = logging.getLogger(__name__)


class NotebookInterface:
    """Implements ModuleInterface protocol"""

    def initialize(self, modes):
        if ImportMode.API in modes:
            import dataall.modules.notebooks.api
        if ImportMode.CDK in modes:
            import dataall.modules.notebooks.cdk

        log.info("Sagemaker notebooks has been imported")

    def has_allocated_resources(self, session, environment_uri):
        return NotebookRepository(session).count_notebooks(environment_uri) > 0

