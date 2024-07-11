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

    @staticmethod
    def invalid_policy_error_msg(
        requestor, permission_type, permissions, resource_type, target_resource, missing_actions, extra_actions
    ):
        requestor = ShareErrorFormatter._stringify(requestor)
        permissions = ShareErrorFormatter._stringify(permissions)
        message = f'Requestor {requestor} has invalid {permission_type} policy: {permissions} for {resource_type} Target: {target_resource}.'
        if missing_actions:
            message += ' Missing actions: {missing_actions}. Not allowed permissions: {extra_actions}'
        if extra_actions:
            message += ' Not allowed permissions: {extra_actions}'
