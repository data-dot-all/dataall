from typing import List, Type, Set
import logging
from dataall.base.loader import ModuleInterface, ImportMode

log = logging.getLogger(__name__)


class MetadataFormsApiModuleInterface(ModuleInterface):
    """Implements ModuleInterface for Metadata Forms GraphQl lambda"""

    @classmethod
    def is_supported(cls, modes):
        return ImportMode.API in modes

    def __init__(self):
        import dataall.modules.metadata_forms.api
        import dataall.modules.metadata_forms.db.enums

    @staticmethod
    def depends_on() -> List[Type['ModuleInterface']]:
        from dataall.modules.datasets_base import DatasetBaseApiModuleInterface

        return [DatasetBaseApiModuleInterface]


class MetadataFormAsyncHandlersModuleInterface(ModuleInterface):
    """Implements ModuleInterface for metadataform async lambda"""

    @staticmethod
    def is_supported(modes: Set[ImportMode]):
        return ImportMode.HANDLERS in modes

    def __init__(self):
        import dataall.modules.metadata_forms.handlers
        import dataall.modules.metadata_forms.db.metadata_form_models
        import dataall.modules.metadata_forms.db.metadata_form_repository
        import dataall.modules.metadata_forms.services.metadata_form_enforcement_service

        log.info('Metadata Form handlers have been imported')
