import logging
import os
import json

from auth_services import AuthServices
from jwt_services import JWTServices

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

"""
Custom Lambda Authorizer Code Performs following,
    1. Fetches the token from Authorizer Header 
    2. Validates the JWT Token
    3. Attaches a Policy to invoke graphQL and search APIs and also context containing userid and email needed for processing API in GraphQL Lambda
    
Custom Lambda Authorizer is attached to the API Gateway. Check the deploy/stacks/lambda_api.py for more details on deployment
"""

OPENID_CONFIG_PATH = os.path.join(os.environ.get('custom_auth_url', ''), '.well-known', 'openid-configuration')
jwt_service = JWTServices(OPENID_CONFIG_PATH)


def lambda_handler(incoming_event, context):
    # Get the Token which is sent in the Authorization Header
    logger.debug(incoming_event)
    auth_token = incoming_event['headers']['Authorization']
    access_token = incoming_event['headers']['accesskeyid']
    if not auth_token or not access_token:
        raise Exception('Unauthorized. Missing identity or access JWT')

    # Validate User is Active with Proper Access Token
    jwt_service.validate_access_token(access_token)

    # Validate JWT
    verified_claims = jwt_service.validate_jwt_token(auth_token)
    if not verified_claims:
        raise Exception('Unauthorized. Token is not valid')
    logger.debug(verified_claims)

    # Generate Allow Policy w/ Context
    effect = 'Allow'
    policy = AuthServices.generate_policy(verified_claims, effect, incoming_event['methodArn'])
    logger.debug(f'Generated policy is {json.dumps(policy)}')
    return policy


# Below Code only used for testing on local development IDE
# the following is useful to make this script executable in both
# AWS Lambda and any other local environments
if __name__ == '__main__':
    # for testing locally you can enter the JWT ID Token here
    id_token = ''
    access_token = ''
    account_id = ''
    api_gw_id = ''
    event = {
        'headers': {'Authorization': id_token, 'accesskeyid': access_token},
        'type': 'TOKEN',
        'methodArn': f'arn:aws:execute-api:us-east-1:{account_id}:{api_gw_id}/prod/POST/graphql/api',
    }
    lambda_handler(event, None)
