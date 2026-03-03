import json
import logging
import os
import urllib.request
import urllib.parse
import base64
from http.cookies import SimpleCookie

logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))


def handler(event, context):
    """Main Lambda handler - routes requests to appropriate function"""
    path = event.get('path', '')
    method = event.get('httpMethod', '')

    if path == '/auth/token-exchange' and method == 'POST':
        return token_exchange_handler(event)
    elif path == '/auth/logout' and method == 'POST':
        return logout_handler(event)
    elif path == '/auth/userinfo' and method == 'GET':
        return userinfo_handler(event)
    else:
        return error_response(404, 'Not Found', event)


def error_response(status_code, message, event=None):
    """Return error response with CORS headers"""
    response = {
        'statusCode': status_code,
        'headers': get_cors_headers(event) if event else {'Content-Type': 'application/json'},
        'body': json.dumps({'error': message}),
    }
    return response


def get_cors_headers(event):
    """Get CORS headers for response"""
    cloudfront_url = os.environ.get('CLOUDFRONT_URL', '')
    return {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': cloudfront_url,
        'Access-Control-Allow-Credentials': 'true',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
    }


def token_exchange_handler(event):
    """Exchange authorization code for tokens and set httpOnly cookies"""
    try:
        body = json.loads(event.get('body', '{}'))
        code = body.get('code')
        code_verifier = body.get('code_verifier')

        if not code or not code_verifier:
            return error_response(400, 'Missing code or code_verifier', event)

        okta_url = os.environ.get('CUSTOM_AUTH_URL', '')
        client_id = os.environ.get('CUSTOM_AUTH_CLIENT_ID', '')
        redirect_uri = os.environ.get('CUSTOM_AUTH_REDIRECT_URL', '')

        if not okta_url or not client_id:
            return error_response(500, 'Missing Okta configuration', event)

        # Call Okta token endpoint
        token_url = f'{okta_url}/v1/token'
        token_data = {
            'grant_type': 'authorization_code',
            'code': code,
            'code_verifier': code_verifier,
            'client_id': client_id,
            'redirect_uri': redirect_uri,
        }

        data = urllib.parse.urlencode(token_data).encode('utf-8')
        req = urllib.request.Request(
            token_url,
            data=data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                tokens = json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            logger.error(f'Token exchange failed: {error_body}')
            return error_response(401, 'Authentication failed. Please try again.', event)

        cookies = build_cookies(tokens)

        return {
            'statusCode': 200,
            'headers': get_cors_headers(event),
            'multiValueHeaders': {'Set-Cookie': cookies},
            'body': json.dumps({'success': True}),
        }

    except Exception as e:
        logger.error(f'Token exchange error: {str(e)}')
        return error_response(500, 'Internal server error', event)


def build_cookies(tokens):
    """Build httpOnly cookies for tokens"""
    cookies = []
    secure = True
    httponly = True
    samesite = 'Lax'
    max_age = 3600  # 1 hour

    for token_name in ['access_token', 'id_token']:
        if tokens.get(token_name):
            cookie = SimpleCookie()
            cookie[token_name] = tokens[token_name]
            cookie[token_name]['path'] = '/'
            cookie[token_name]['secure'] = secure
            cookie[token_name]['httponly'] = httponly
            cookie[token_name]['samesite'] = samesite
            cookie[token_name]['max-age'] = max_age
            cookies.append(cookie[token_name].OutputString())

    return cookies


def logout_handler(event):
    """Clear all auth cookies"""
    cookies = []
    for cookie_name in ['access_token', 'id_token', 'refresh_token']:
        cookie = SimpleCookie()
        cookie[cookie_name] = ''
        cookie[cookie_name]['path'] = '/'
        cookie[cookie_name]['max-age'] = 0
        cookies.append(cookie[cookie_name].OutputString())

    return {
        'statusCode': 200,
        'headers': get_cors_headers(event),
        'multiValueHeaders': {'Set-Cookie': cookies},
        'body': json.dumps({'success': True}),
    }


def userinfo_handler(event):
    """Return user info from id_token cookie"""
    try:
        cookie_header = event.get('headers', {}).get('Cookie') or event.get('headers', {}).get('cookie', '')
        cookies = SimpleCookie()
        cookies.load(cookie_header)

        id_token_cookie = cookies.get('id_token')
        if not id_token_cookie:
            return error_response(401, 'Not authenticated', event)

        id_token = id_token_cookie.value

        # Decode JWT payload
        parts = id_token.split('.')
        if len(parts) != 3:
            return error_response(401, 'Invalid token format', event)

        payload = parts[1]
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += '=' * padding

        decoded = base64.urlsafe_b64decode(payload)
        claims = json.loads(decoded)

        email_claim = os.environ.get('CLAIMS_MAPPING_EMAIL', 'email')
        user_id_claim = os.environ.get('CLAIMS_MAPPING_USER_ID', 'sub')

        email = claims.get(email_claim, claims.get('email', claims.get('sub', '')))
        user_id = claims.get(user_id_claim, claims.get('sub', ''))

        return {
            'statusCode': 200,
            'headers': get_cors_headers(event),
            'body': json.dumps(
                {
                    'email': email,
                    'name': claims.get('name', email),
                    'sub': user_id,
                }
            ),
        }

    except Exception as e:
        logger.error(f'Userinfo error: {str(e)}')
        return error_response(500, 'Internal server error', event)
