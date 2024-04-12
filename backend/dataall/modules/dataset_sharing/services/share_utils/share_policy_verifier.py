import json
import logging

logger = logging.getLogger(__name__)

from dataall.base.aws.iam import IAM


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
