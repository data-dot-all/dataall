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
    if not auth_token:
        raise Exception('Unauthorized. Missing identity or access JWT')

    # Validate User is Active with Proper Access Token
    user_info = jwt_service.validate_access_token(auth_token)

    # Validate JWT
    verified_claims = jwt_service.validate_jwt_token(auth_token[7:])
    if not verified_claims:
        raise Exception('Unauthorized. Token is not valid')
    logger.debug(verified_claims)

    # Generate Allow Policy w/ Context
    effect = 'Allow'
    verified_claims.update(user_info)
    policy = AuthServices.generate_policy(verified_claims, effect, incoming_event['methodArn'])
    logger.debug(f'Generated policy is {json.dumps(policy)}')
    print(f'Generated policy is {json.dumps(policy)}')
    return policy


# Below Code only used for testing on local development IDE
# the following is useful to make this script executable in both
# AWS Lambda and any other local environments
if __name__ == '__main__':
    # for testing locally you can enter the JWT ID Token here
    #
    access_token = 'Bearer eyJraWQiOiJtYTJ6SUxrbVMtQW1qZzZwVGtqZjhkN3JxY1FaNWE2eWtLS3dGQkFZckJBIiwidHlwIjoiYXBwbGljYXRpb25cL29rdGEtaW50ZXJuYWwtYXQrand0IiwiYWxnIjoiUlMyNTYifQ.eyJ2ZXIiOjEsImp0aSI6IkFULm9DSERGSHpVdGFUeTFDQXBENWF3amZRMEdyUzNPcEpyNE93czdnM3JKUXciLCJpc3MiOiJodHRwczovL2Rldi0zNzAxMTAxMC5va3RhLmNvbSIsImF1ZCI6Imh0dHBzOi8vZGV2LTM3MDExMDEwLm9rdGEuY29tIiwic3ViIjoibm9haHBhaWdAYW1hem9uLmNvbSIsImlhdCI6MTczMDkyNTQ1MiwiZXhwIjoxNzMwOTI5MDUyLCJjaWQiOiIwb2FkcndpcmVxcldoanFYaTVkNyIsInVpZCI6IjAwdWRydTNtNTZWS3hnWEtKNWQ3Iiwic2NwIjpbIm9wZW5pZCIsImVtYWlsIiwicHJvZmlsZSJdLCJhdXRoX3RpbWUiOjE3MzA5MjU0NTF9.uFZ123U7nbu6rN0L9WB2EZQTEZCnMcYOV_6uS4XRb8TAREcat-Kk88rLXONLwNWSaLaqGXOsr1tC1bd9FdTXyWG9WmVkihep8un_tmy1V410vEBtzXes6nqsr4-QZsx7csrWWtDetm4T7Smtl621z4isL8ePdYtkWe_2SELJjiOpr8qQ8pXMVEwMY8kiu-VuZHUXNnFGvrIRtNytsNzFVunbQxOX58uCq_J5eU7MRbj0tBAYqLXgXrj1iskb17uGHL4IqIWl1Te6qk05bLMZ9RrySEpyuCmYDPIgFpUZNiewLUNgPTNb4I8wrKycTpNfEEhTiLNxjo7QA5y2stTrFg'
    account_id = ''
    api_gw_id = ''
    event = {
        'headers': {'Authorization': access_token},
        'type': 'TOKEN',
        'methodArn': f'arn:aws:execute-api:us-east-1:{account_id}:{api_gw_id}/prod/POST/graphql/api',
    }
    lambda_handler(event, None)
