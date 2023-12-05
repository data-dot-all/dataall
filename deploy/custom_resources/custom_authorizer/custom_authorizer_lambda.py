import logging
import os

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

def lambda_handler(incoming_event, context):
    # Get the Token which is sent in the Authorization Header
    auth_token = incoming_event['headers']['Authorization']
    if not auth_token:
        raise Exception('Unauthorized . Token not found')

    verified_claims = JWTServices.validate_jwt_token(auth_token)
    logger.debug(verified_claims)
    if not verified_claims:
        raise Exception('Unauthorized. Token is not valid')

    effect = 'Allow'
    policy = AuthServices.generate_policy(verified_claims, effect, incoming_event['methodArn'])
    logger.debug('Generated policy is ', policy)
    return policy


# Below Code only used for testing on local development IDE
# the following is useful to make this script executable in both
# AWS Lambda and any other local environments
if __name__ == '__main__':
    # for testing locally you can enter the JWT ID Token here
    token = ""
    event = {
        "type": "TOKEN",
        "Authorization": token,
        "methodArn": "arn:aws:execute-api:us-east-1:012356677990:abc1cv8nko/prod/POST/graphql/api"
    }
    lambda_handler(event, None)