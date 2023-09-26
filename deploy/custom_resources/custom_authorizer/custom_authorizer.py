import json
import os
import requests
import boto3
from jose import jwk
from jose.jwt import get_unverified_header, decode, ExpiredSignatureError, JWTError
import logging


logger = logging.getLogger()
logger.setLevel(logging.INFO)

ssm = boto3.client('ssm')

USER_POOL_ID = os.environ["USER_POOL_ID"]
CLIENT_ID = os.environ["CLIENT_ID"]

ISSUER_CONFIGS = {
    f"https://cognito-idp.us-east-1.amazonaws.com/{USER_POOL_ID}": {
        "jwks_uri": f"https://cognito-idp.us-east-1.amazonaws.com/{USER_POOL_ID}/.well-known/jwks.json",
        "allowed_audiences": CLIENT_ID,
    },
}
ALLOWED_API_RESOURCE_NAMES = ["graphql", "search"]
issuer_keys = {}
# instead of re-downloading the public keys every time
# we download them only on cold start
# https://aws.amazon.com/blogs/compute/container-reuse-in-lambda/
for issuer, issuer_config in ISSUER_CONFIGS.items():
    jwks_response = requests.get(issuer_config["jwks_uri"])
    jwks_response.raise_for_status()
    jwks: dict = jwks_response.json()
    for key in jwks["keys"]:
        value = {"issuer": issuer, "audience": issuer_config["allowed_audiences"], "jwk": jwk.construct(key), "public_key": jwk.construct(key).public_key()}
        issuer_keys.update({key["kid"]: value})

# Using the following options to validate the JWT token
# Only modification from default is to turn off verify_at_hash
jwt_options = {
    "verify_signature": True,
    "verify_aud": True,
    "verify_iat": True,
    "verify_exp": True,
    "verify_nbf": True,
    "verify_iss": True,
    "verify_sub": True,
    "verify_jti": True,
    "verify_at_hash": False,
    "require_aud": True,
    "require_iat": False,
    "require_exp": True,
    "require_nbf": False,
    "require_iss": True,
    "require_sub": True,
    "require_jti": False,
    "require_at_hash": True,
    "leeway": 0,
}


def validate_jwt_token(jwt_token):
    try:
        # Decode and verify the JWT token
        header = get_unverified_header(jwt_token)
        kid = header['kid']
        if kid not in issuer_keys:
            print('Public key not found in provided set of keys')
            raise Exception('Unauthorized')
        public_key = issuer_keys.get(kid)
        payload = decode(jwt_token, public_key.get('jwk'), algorithms=['RS256', 'HS256'],
                         issuer=public_key.get('issuer'), audience=public_key.get('audience'), options={"verify_at_hash": False})

        return payload
    except ExpiredSignatureError:
        logger.error("JWT token has expired.")
        return None
    except JWTError as e:
        logger.error(f"JWT token validation failed: {str(e)}")
        return None


def lambda_handler(incoming_event, context):
    auth_token = incoming_event.get("headers", {}).get('Authorization',None)
    if not auth_token:
        raise Exception('Unauthorized')
    verified_claims = validate_jwt_token(auth_token)
    if not verified_claims:
        raise Exception('Unauthorized')
    effect = 'Allow'
    policy = generate_policy(verified_claims, effect, incoming_event['methodArn'])
    print('generated policy is ', policy)

    try:
        param_value = ssm.get_parameter(Name='dataall/reauth/operations')['Parameter']['Value']

    except Exception as e:
        print(e)

    return policy


# Input example arn:aws:execute-api:us-east-1:012356677990:abc1cv8nko/prod/POST/graphql/api
# Output example arn:aws:execute-api:us-east-1:012356677990:abc1cv8nko/*/POST/graphql/api
def generate_resource_str(resource, api_resource_name):
    resource_list = resource.split(':')
    api_gateway_arn = resource_list[5].split('/')
    api_gateway_arn[1] = '*'
    api_gateway_arn[3] = api_resource_name
    resource_list[5] = "/".join(api_gateway_arn)
    return ":".join(resource_list)


def generate_policy(verified_claims: dict, effect, incoming_resource_str: str):
    # This is required since API Gateway does not support nested claims
    principal_id = verified_claims['sub']
    if 'cognito:groups' in verified_claims:
        verified_claims['cognito:groups'] = ",".join(verified_claims.get('cognito:groups'))

    for claim_name, claim_value in verified_claims.items():
        if type(claim_value) is list:
            verified_claims.update({claim_name: json.dumps(claim_value)})

    context = {**verified_claims}

    context.update({
        'userId': principal_id,
        'custom_authorizer': 'true',
    })
    policy_statement = []

    for api_resource_name in ALLOWED_API_RESOURCE_NAMES:
        policy_statement.append({
            'Action': 'execute-api:Invoke',
            'Effect': effect,
            'Resource': generate_resource_str(incoming_resource_str, api_resource_name)
        })

    policy = {
        'principalId': principal_id,
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': policy_statement
        },
        'context': context
    }

    return policy


# the following is useful to make this script executable in both
# AWS Lambda and any other local environments
if __name__ == '__main__':
    # for testing locally you can enter the JWT ID Token here
    token = ""
    event = {
        "type": "REQUEST",
        "headers": {
            "Authorization": token
        },
        "methodArn": "arn:aws:execute-api:us-east-1:012356677990:abc1cv8nko/prod/POST/graphql/api"
    }
    lambda_handler(event, None)
