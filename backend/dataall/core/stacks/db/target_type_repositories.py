import logging

from dataall.base.db import exceptions
from dataall.core.permissions.services.environment_permissions import (
    GET_ENVIRONMENT,
    UPDATE_ENVIRONMENT,
)
from dataall.core.permissions.services.tenant_permissions import MANAGE_ENVIRONMENTS

logger = logging.getLogger(__name__)


class TargetType:
    """Resolves the read/write permissions for different type of resources (target types)"""

    _TARGET_TYPES = {}

    def __init__(self, name, read_permission, write_permission, tenant_permission):
        self.name = name
        self.read_permission = read_permission
        self.write_permission = write_permission
        self.tenant_permission = tenant_permission

        TargetType._TARGET_TYPES[name] = self

    @staticmethod
    def get_resource_update_permission_name(target_type):
        TargetType.is_supported_target_type(target_type)
        return TargetType._TARGET_TYPES[target_type].write_permission

    @staticmethod
    def get_resource_read_permission_name(target_type):
        TargetType.is_supported_target_type(target_type)
        return TargetType._TARGET_TYPES[target_type].read_permission

    @staticmethod
    def get_resource_tenant_permission_name(target_type):
        TargetType.is_supported_target_type(target_type)
        return TargetType._TARGET_TYPES[target_type].tenant_permission

    @staticmethod
    def is_supported_target_type(target_type):
        if target_type not in TargetType._TARGET_TYPES:
            raise exceptions.InvalidInput(
                'targetType',
                target_type,
                ' or '.join(TargetType._TARGET_TYPES.keys()),
            )


TargetType('environment', GET_ENVIRONMENT, UPDATE_ENVIRONMENT, MANAGE_ENVIRONMENTS)
