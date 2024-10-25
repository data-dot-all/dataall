import logging
from typing import Callable, Type

logger = logging.getLogger(__name__)


class ShareErrorFormatter:
    @staticmethod
    def _stringify(param):
        if isinstance(param, list):
            param = ','.join(param)
        return param

    @staticmethod
    def dne_error_msg(resource_type, target_resource):
        return f'{resource_type} Target Resource does not exist: {target_resource}'

    @staticmethod
    def wrong_status_error_msg(resource_type, target_resource, status):
        return f'{resource_type} Target Resource {target_resource} in wrong status: {status}'

    @staticmethod
    def missing_permission_error_msg(requestor, permission_type, permissions, resource_type, target_resource):
        requestor = ShareErrorFormatter._stringify(requestor)
        permissions = ShareErrorFormatter._stringify(permissions)
        return f'Requestor {requestor} missing {permission_type} permissions: {permissions} for {resource_type} Target: {target_resource}'

    @staticmethod
    def not_allowed_permission_error_msg(requestor, permission_type, permissions, resource_type, target_resource):
        requestor = ShareErrorFormatter._stringify(requestor)
        permissions = ShareErrorFormatter._stringify(permissions)
        return f'Requestor {requestor} has not allowed {permission_type} permissions: {permissions} for {resource_type} Target: {target_resource}'


def execute_and_suppress_exception(func: Callable, exc: Type[Exception] = Exception, *args, **kwargs):
    try:
        func(*args, **kwargs)
    except exc:
        logger.exception('')
