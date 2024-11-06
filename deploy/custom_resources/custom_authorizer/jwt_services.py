import os

import requests
import jwt

import logging

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))


# Options to validate the JWT token
# Only modification from default is to turn off verify_at_hash as we don't provide the access token for this validation
jwt_options = {
    'verify_signature': True,
    'verify_aud': True,
    'verify_iat': True,
    'verify_exp': True,
    'verify_nbf': True,
    'verify_iss': True,
    'verify_sub': True,
    'verify_jti': True,
    'verify_at_hash': True,
    'require': ['aud', 'iat', 'exp', 'iss', 'sub', 'jti'],  # "nbf", "at_hash"
}


class JWTServices:
    @staticmethod
    def _fetch_openid_url(key):
        response = requests.get(f'{os.environ.get("custom_auth_url")}/.well-known/openid-configuration')
        response.raise_for_status()
        return response.json().get(key)

    @staticmethod
    def validate_jwt_token(jwt_token):
        try:
            # get JWK URI from OpenId Configuration
            jwks_url = JWTServices._fetch_openid_url('jwks_uri')

            # Init pyJWT.JWKClient with JWK URI
            jwks_client = jwt.PyJWKClient(jwks_url)

            # get signing_key from JWT
            signing_key = jwks_client.get_signing_key_from_jwt(jwt_token)

            # Decode and Verify JWT
            payload = jwt.decode(
                jwt_token,
                signing_key.key,
                algorithms=['RS256', 'HS256'],
                issuer=os.environ.get('custom_auth_url'),
                audience=os.environ.get('custom_auth_client'),
                leeway=0,
                options=jwt_options,
            )
            return payload
        except jwt.exceptions.ExpiredSignatureError:
            logger.error('JWT token has expired.')
            return None
        except jwt.exceptions.PyJWTError as e:
            logger.error(f'JWT token validation failed: {str(e)}')
            return None
        except Exception as e:
            logger.error(f'Failed to validate token - {str(e)}')
            return None

    @staticmethod
    def validate_access_token(access_token):
        # get JWK UserInfo URI from OpenId Configuration
        user_info_url = JWTServices._fetch_openid_url('userinfo_endpoint')
        r = requests.get(user_info_url, headers={'Authorization': access_token})
        r.raise_for_status()
        logger.debug(r.json())
