import json

from dataall.base.services.service_provider_factory import ServiceProviderFactory


def get_cognito_groups(claims):
    if not claims:
        raise ValueError(
            'Received empty claims. ' 'Please verify authorizer configuration',
            claims,
        )
    groups = list()
    saml_groups = claims.get('custom:saml.groups', '')
    translation_table = str.maketrans({'[': None, ']': None, ', ': ','})
    if len(saml_groups):
        groups = saml_groups.translate(translation_table).split(',')
    cognito_groups = claims.get('cognito:groups', '')
    if len(cognito_groups):
        groups.extend(cognito_groups.split(','))
    return groups


def get_custom_groups(user_id):
    service_provider = ServiceProviderFactory.get_service_provider_instance()
    return service_provider.get_groups_for_user(user_id)


def send_unauthorized_response(query, message=''):
    response = {
        'data': {query.get('operationName', 'operation'): None},
        'errors': [
            {
                'message': message,
                'locations': None,
                'path': [query.get('operationName', '')],
            }
        ],
    }
    return {
        'statusCode': 401,
        'headers': {
            'content-type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Methods': '*',
        },
        'body': json.dumps(response),
    }
