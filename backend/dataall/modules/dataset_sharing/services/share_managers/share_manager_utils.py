import logging
import json

from dataall.base.aws.iam import IAM

logger = logging.getLogger(__name__)


class SharePolicyVerifier:
    @staticmethod
    def remove_malformed_principal(policy: str, target_sids, account_id, region) -> str:
        logger.info(f'Malformed Policy: {policy}')
        policy = json.loads(policy)
        statements = policy['Statement']
        for statement in statements:
            if statement.get('Sid', 'no-sid') in target_sids:
                new_principal_list = statement['Principal']['AWS'][:]
                IAM.remove_invalid_role_ids(account_id, region, new_principal_list)
                statement['Principal']['AWS'] = new_principal_list
        policy['Statement'] = statements
        logger.info(f'Fixed Policy: {json.dumps(policy)}')
        return json.dumps(policy)


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
