import json
import os

import requests
from jose import jwk
from jose.jwt import get_unverified_header, decode, ExpiredSignatureError, JWTError
import logging

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Configs required to fetch public keys from JWKS
ISSUER_CONFIGS = {
    f'{os.environ.get("custom_auth_url")}': {
        "jwks_uri": f'{os.environ.get("custom_auth_jwks_url")}',
        "allowed_audiences": f'{os.environ.get("custom_auth_client")}',
    },
}

issuer_keys = {}

# instead of re-downloading the public keys every time
# we download them only on cold start
# https://aws.amazon.com/blogs/compute/container-reuse-in-lambda/
def fetch_public_keys():
    try:
        for issuer, issuer_config in ISSUER_CONFIGS.items():
            jwks_response = requests.get(issuer_config["jwks_uri"])
            jwks_response.raise_for_status()
            jwks: dict = jwks_response.json()
            for key in jwks["keys"]:
                value = {"issuer": issuer, "audience": issuer_config["allowed_audiences"], "jwk": jwk.construct(key),
                         "public_key": jwk.construct(key).public_key()}
                issuer_keys.update({key["kid"]: value})
    except Exception as e:
        raise Exception(f'Unable to fetch public keys due to {str(e)}')

fetch_public_keys()

# Options to validate the JWT token
# Only modification from default is to turn off verify_at_hash as we don't provide the access token for this validation
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
    "require_iat": True,
    "require_exp": True,
    "require_nbf": False,
    "require_iss": True,
    "require_sub": True,
    "require_jti": True,
    "require_at_hash": False,
    "leeway": 0,
}

class JWTServices():
    @staticmethod
    def validate_jwt_token(jwt_token):
        try:
            # Decode and verify the JWT token
            header = get_unverified_header(jwt_token)
            kid = header['kid']
            if kid not in issuer_keys:
                logger.info('Public key not found in provided set of keys')
                # Retry Fetching the public certificates again in case rotation occurs and lambda has cached the publicKeys
                fetch_public_keys()
                if kid not in issuer_keys:
                    raise Exception('Unauthorized')
            public_key = issuer_keys.get(kid)
            payload = decode(jwt_token, public_key.get('jwk'), algorithms=['RS256', 'HS256'],
                             issuer=public_key.get('issuer'), audience=public_key.get('audience'), options=jwt_options)

            return payload
        except ExpiredSignatureError:
            logger.error("JWT token has expired.")
            return None
        except JWTError as e:
            logger.error(f"JWT token validation failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f'Failed to validate token - {str(e)}')
            return None
