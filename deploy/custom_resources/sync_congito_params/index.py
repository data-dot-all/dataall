import os

import boto3
from botocore.exceptions import ClientError

ssm_us_east_1 = boto3.client('ssm', region_name='us-east-1')
ssm = boto3.client('ssm', region_name=os.environ.get('AWS_REGION', 'eu-west-1'))


def on_event(event, context):
    print('Received', event)
    request_type = event['RequestType']
    if request_type == 'Create':
        return on_create(event)
    if request_type == 'Update':
        return on_update(event)
    if request_type == 'Delete':
        return on_delete(event)
    raise Exception('Invalid request type: %s' % request_type)


def on_create(event):
    print('**Sync Cognito Parameters')
    parameters = get_parameters(ssm, f'/dataall/{event["ResourceProperties"]["envname"]}/cognito')
    print('all cognito params', parameters)
    response_data = sync_parameter_store(parameters)
    return response_data


def on_update(event):
    on_create(event)


def on_delete(event):
    print('Received delete event')


def sync_parameter_store(parameters):
    print(f'Found parameters -- {parameters}')
    for _parameter_store in parameters:
        cross_region_param_exists = False
        try:
            ssm_us_east_1.put_parameter(
                Name=_parameter_store['Name'],
                Description=f'mirror of {_parameter_store["Name"]} in eu-west-1 ',
                Value=_parameter_store['Value'],
                Type='String',
                Overwrite=True,
            )
            print(f'Synced param {_parameter_store}')
        except ClientError as e:
            print(f'Error Syncing param {_parameter_store} due to {e}')
    return 'ParameterSync'


def get_parameters(client, path):
    parameters = []
    more = True
    token = None
    while more:
        if token is None:
            response = client.get_parameters_by_path(Path=path, Recursive=True, MaxResults=10)
        else:
            response = client.get_parameters_by_path(Path=path, Recursive=True, MaxResults=10, NextToken=token)
        for param in response['Parameters']:
            parameters.append(param)
        token = response.get('NextToken')
        more = False if token is None else True
    return parameters


def delete_parameter_store(parameters):
    print(f'Delete Config -- {parameters}')
    for _parameter_store in parameters:
        try:
            ssm_us_east_1.delete_parameter(Name=_parameter_store['Name'])
        except ClientError as e:
            print(f'Failed to delete param {_parameter_store} due to {e}')
    return 'ParameterDeleted'
