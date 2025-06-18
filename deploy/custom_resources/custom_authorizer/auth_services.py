import json
import logging
import os

EMAIL_CLAIM = os.getenv('email')
USER_ID_CLAIM = os.getenv('user_id')

ALLOWED_API_RESOURCE_NAMES = ['graphql', 'search']

logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))


class AuthServices:
    # Input example arn:aws:execute-api:us-east-1:012356677990:abc1cv8nko/prod/POST/XXXXXXX/api
    # Output example arn:aws:execute-api:us-east-1:012356677990:abc1cv8nko/prod/POST/graphql/api
    @staticmethod
    def generate_resource_str(resource, api_resource_name):
        resource_list = resource.split(':')
        api_gateway_arn = resource_list[5].split('/')
        api_gateway_arn[3] = api_resource_name
        resource_list[5] = '/'.join(api_gateway_arn)
        return ':'.join(resource_list)

    @staticmethod
    def generate_deny_policy(incoming_resource_str: str):
        return AuthServices.generate_policy(
            {'sub': None, EMAIL_CLAIM: None, USER_ID_CLAIM: None}, 'Deny', incoming_resource_str
        )

    # Generates Policy document containing policy to allow the API invocation for allowed API Endpoints
    # Also attaches the claims which are present in the token
    # Policy document and principal_id are two required items when using custom authorizer lamda in API gateway
    @staticmethod
    def generate_policy(verified_claims: dict, effect, incoming_resource_str: str):
        # principal_id is a required attribute which needs to be provided by custom authorizer
        principal_id = verified_claims['sub']

        # Attach a claim called 'email'. This is needed by Api Handler
        verified_claims['email'] = verified_claims[EMAIL_CLAIM]

        for claim_name, claim_value in verified_claims.items():
            if isinstance(claim_value, list):
                verified_claims.update({claim_name: ','.join(claim_value)})

        context = {**verified_claims}

        context.update(
            {
                'user_id': verified_claims[USER_ID_CLAIM],
                'custom_authorizer': 'true',
            }
        )

        policy_statement = []

        for api_resource_name in ALLOWED_API_RESOURCE_NAMES:
            policy_statement.append(
                {
                    'Action': 'execute-api:Invoke',
                    'Effect': effect,
                    'Resource': AuthServices.generate_resource_str(incoming_resource_str, api_resource_name),
                }
            )

        policy = {
            'principalId': principal_id,
            'policyDocument': {'Version': '2012-10-17', 'Statement': policy_statement},
            'context': context,
        }

        logger.debug(f'Generated policy is {json.dumps(policy)}')

        return policy
