import logging
import os

from requests import HTTPError

from auth_services import AuthServices
from jwt_services import JWTServices

logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

"""
Custom Lambda Authorizer Code Performs following,
    1. Fetches the token from Authorizer Header 
    2. Validates the JWT Token
    3. Attaches a Policy to invoke graphQL and search APIs and also context containing userid and email needed for processing API in GraphQL Lambda
    
Custom Lambda Authorizer is attached to the API Gateway. Check the deploy/stacks/lambda_api.py for more details on deployment
"""

OPENID_CONFIG_PATH = os.path.join(os.environ['custom_auth_url'], '.well-known', 'openid-configuration')
JWT_SERVICE = JWTServices(OPENID_CONFIG_PATH)


def lambda_handler(incoming_event, context):
    # Get the Token - first try Cookie header, then Authorization header
    logger.debug(incoming_event)
    headers = incoming_event.get('headers', {})

    # Try to get access_token from Cookie header first (for cookie-based auth)
    auth_token = None
    cookie_header = headers.get('Cookie') or headers.get('cookie', '')

    if cookie_header:
        # Parse cookies to find access_token
        from http.cookies import SimpleCookie

        cookies = SimpleCookie()
        cookies.load(cookie_header)
        access_token_cookie = cookies.get('access_token')
        if access_token_cookie:
            # Add Bearer prefix for consistency with existing validation
            auth_token = f'Bearer {access_token_cookie.value}'
            logger.debug('Using access_token from Cookie header')

    # Fallback to Authorization header (for backward compatibility)
    if not auth_token:
        auth_token = headers.get('Authorization') or headers.get('authorization')
        if auth_token:
            logger.debug('Using token from Authorization header')

    if not auth_token:
        logger.warning('No authentication token found in Cookie or Authorization header')
        return AuthServices.generate_deny_policy(incoming_event['methodArn'])

    # Validate User is Active with Proper Access Token
    try:
        user_info = JWT_SERVICE.validate_access_token(auth_token)
    except HTTPError as e:
        logger.warning('Failed to validate access token', exc_info=True)
        if e.response.status_code in [
            401,  # Unauthorized
            403,  # Throttling
        ]:
            return AuthServices.generate_deny_policy(incoming_event['methodArn'])
        else:
            raise e  # Unexpected exceptions

    # Validate JWT
    # Note: Removing the 7 Prefix Chars for 'Bearer ' from JWT
    verified_claims = JWT_SERVICE.validate_jwt_token(auth_token[7:])
    if not verified_claims:
        logger.warning('Failed to validate jwt token', exc_info=True)
        return AuthServices.generate_deny_policy(incoming_event['methodArn'])
    logger.debug(verified_claims)

    # Generate Allow Policy w/ Context
    effect = 'Allow'
    verified_claims.update(user_info)
    policy = AuthServices.generate_policy(verified_claims, effect, incoming_event['methodArn'])
    return policy


# Below Code only used for testing on local development IDE
# the following is useful to make this script executable in both
# AWS Lambda and any other local environments
if __name__ == '__main__':
    # for testing locally you can enter the JWT ID Token here
    #
    access_token = os.environ['access_token']
    account_id = ''
    api_gw_id = ''
    event = {
        'headers': {'Authorization': access_token},
        'type': 'TOKEN',
        'methodArn': f'arn:aws:execute-api:us-east-1:{account_id}:{api_gw_id}/prod/POST/graphql/api',
    }
    print(lambda_handler(event, None))
