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


# the following is useful to make this script executable in both
# AWS Lambda and any other local environments
if __name__ == '__main__':
    # for testing locally you can enter the JWT ID Token here
    token = "eyJraWQiOiJyUkU3U2RHQTVpT0EyZm9SSmNhTHIzLUd2QUJoM0JLT1ZRVVRVcGNwNjZrIiwiYWxnIjoiUlMyNTYifQ.eyJzdWIiOiIwMHU4bXltaGVuMWNXVmhSbjFkNyIsIm5hbWUiOiJUZWphcyBSYWpvcGFkaHllIiwidmVyIjoxLCJpc3MiOiJodHRwczovL291cnlhaG9vLXFhLm9rdGFwcmV2aWV3LmNvbS9vYXV0aDIvYXVzMmMxanp0b0lZSkNNZ28xZDciLCJhdWQiOiIwb2E4NW9jM3F4c3JSSWF1TDFkNyIsImlhdCI6MTY5OTQ1NzkyNSwiZXhwIjoxNjk5NDYxNTI1LCJqdGkiOiJJRC5TOE1ad3VvSmRyb25mMUNBSHlUbU1ueVc4aFBXQlZvUEhRbFU0U1lSQkVnIiwiYW1yIjpbIm1mYSIsIm90cCIsInB3ZCJdLCJpZHAiOiIwMG8xcTJ6YTZxTzFVVUNFQTFkNyIsInByZWZlcnJlZF91c2VybmFtZSI6InRyYWpvcGFkaHllIiwiYXV0aF90aW1lIjoxNjk5NDU3OTI0LCJhdF9oYXNoIjoiSXdiaHhJeG96X051a2FCRkdGdTZKZyIsImNvdW50cnlDb2RlIjoiVVMiLCJsYXN0X25hbWUiOiJSYWpvcGFkaHllIiwicHJpbWFyeV9lbWFpbCI6InRlamFzLnJham9wYWRoeWVAeWFob29pbmMuY29tIiwic2hvcnRfaWQiOiJ0cmFqb3BhZGh5ZSIsImRpc3BsYXlfbmFtZSI6IlRlamFzIFJham9wYWRoeWUiLCJmaXJzdF9uYW1lIjoiVGVqYXMifQ.EWD27A-TC3ouB-qsTQv_omyKpV4s7ZHTspAQIMVoFcsBOuA26tf_Fa1cwi3w1YBNR3C27XB95HB6b3ZQkja8QCgqkQ9ykhfnhzBGqRF3rP-RkCt0jmRpJNY-nkAmdV0-AkA0iPkXtQPFAfr0pMEwGsr529Gn4wvyQZHEa91O3HDypFqGekRfcPJdD-6lfd2csbTwLRsFUcRutZo3FJ7aMwjp8PRLGyaFCvNNFh7uieBEHJ6-qAMz8cwUedL6dadtOa7FTH3mZFgdMBzc_NJV3xlga6nj_4MGbzPSDRDpeWcNV_AWtHccJGp_j4DbwE2z3D43DLuk3qePfSMUcUOYSQ"
    event = {
        "type": "TOKEN",
        "Authorization": token,
        "methodArn": "arn:aws:execute-api:us-east-1:012356677990:abc1cv8nko/prod/POST/graphql/api"
    }
    lambda_handler(event, None)