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
    def __init__(self, openid_config_path):
        # Get OpenID Config JSON
        self.openid_config = self._fetch_openid_config(openid_config_path)

        # Init pyJWT.JWKClient with JWK URI
        self.jwks_client = jwt.PyJWKClient(self.openid_config.get('jwks_uri'))

    def _fetch_openid_config(self, openid_config_path):
        response = requests.get(openid_config_path)
        response.raise_for_status()
        return response.json()

    def validate_jwt_token(self, jwt_token):
        try:
            # get signing_key from JWT
            signing_key = self.jwks_client.get_signing_key_from_jwt(jwt_token)

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

    def validate_access_token(self, access_token):
        # get UserInfo URI from OpenId Configuration
        user_info_url = self.openid_config.get('userinfo_endpoint')
        r = requests.get(user_info_url, headers={'Authorization': access_token})
        r.raise_for_status()
        logger.debug(r.json())
