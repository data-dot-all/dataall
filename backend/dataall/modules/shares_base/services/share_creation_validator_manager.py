import logging
from typing import Any, Dict
from abc import ABC, abstractmethod
from dataall.modules.shares_base.services.shares_enums import ShareableType

log = logging.getLogger(__name__)


class SharesCreationValidatorInterface(ABC):
    @abstractmethod
    def validate_share_object_creation(self, *args, **kwargs) -> bool:
        """Executes checks when a share request gets created"""
        ...

class ShareCreationValidatorManager:
    SHARING_VALIDATORS: Dict[ShareableType, SharesCreationValidatorInterface] = {}

    @classmethod
    def register_processor(cls, type: ShareableType, validator: SharesCreationValidatorInterface) -> None:
        cls.SHARING_VALIDATORS[type] = validator

    @classmethod
    def get_validator_by_item_type(cls, type: str) -> SharesCreationValidatorInterface:
        for shareable_type, validator in cls.SHARING_VALIDATORS.items():
            if shareable_type.value == type:
                return validator
