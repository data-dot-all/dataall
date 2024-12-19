import os

import requests
import jwt

import logging

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))


# Options to validate the JWT token
# Only modification from default is to turn off verify_aud as Cognito Access Token does not provide this claim
jwt_options = {
    'verify_signature': True,
    'verify_aud': False,
    'verify_iat': True,
    'verify_exp': True,
    'verify_nbf': True,
    'verify_iss': True,
    'verify_sub': True,
    'verify_jti': True,
    'require': ['iat', 'exp', 'iss', 'sub', 'jti'],
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

    def validate_jwt_token(self, jwt_token) -> dict:
        try:
            # get signing_key from JWT
            signing_key = self.jwks_client.get_signing_key_from_jwt(jwt_token)

            # Decode and Verify JWT
            payload = jwt.decode(
                jwt_token,
                signing_key.key,
                algorithms=['RS256', 'HS256'],
                issuer=os.environ['custom_auth_url'],
                audience=os.environ.get('custom_auth_client'),
                leeway=0,
                options=jwt_options,
            )

            # verify client_id if Cognito JWT
            if 'client_id' in payload and payload['client_id'] != os.environ.get('custom_auth_client'):
                raise Exception('Invalid Client ID in JWT Token')

            # verify cid for other IdPs
            if 'cid' in payload and payload['cid'] != os.environ.get('custom_auth_client'):
                raise Exception('Invalid Client ID in JWT Token')

            return payload
        except jwt.exceptions.ExpiredSignatureError as e:
            logger.error('JWT token has expired.')
            raise e
        except jwt.exceptions.PyJWTError as e:
            logger.error(f'JWT token validation failed: {str(e)}')
            raise e
        except Exception as e:
            logger.error(f'Failed to validate token - {str(e)}')
            raise e

    def validate_access_token(self, access_token) -> dict:
        # get UserInfo URI from OpenId Configuration
        user_info_url = self.openid_config.get('userinfo_endpoint')
        r = requests.get(user_info_url, headers={'Authorization': access_token})
        r.raise_for_status()
        logger.debug(r.json())
        return r.json()
