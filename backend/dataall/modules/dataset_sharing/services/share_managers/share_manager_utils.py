import logging

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
    def missing_permission_error_msg(requestor, permission_type, permissions, resource_type, target_resource):
        requestor = ShareErrorFormatter._stringify(requestor)
        permissions = ShareErrorFormatter._stringify(permissions)
        return f'Requestor {requestor} missing {permission_type} permissions: {permissions} for {resource_type} Target: {target_resource}'
