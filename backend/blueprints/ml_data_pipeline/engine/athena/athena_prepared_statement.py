""" Makes athena prepared statement.
Since there is no CloudFormation call for it we have to create a custom resource
(scope, id, *, policy, function_name=None, install_latest_aws_sdk=None, log_retention=None, on_create=None, on_delete=None, on_update=None, resource_type=None, role=None, timeout=None)
"""

from aws_cdk.custom_resources import AwsCustomResource
from aws_cdk.custom_resources import (
    AwsCustomResourcePolicy,
    AwsSdkCall,
    PhysicalResourceId,
)
import boto3

client = boto3.client('athena')


def get_on_create_update(resource, query):
    config = resource.get('config', {})
    name = resource['name']
    workgroup = config['workgroup']
    prepared_statements = client.list_prepared_statements(WorkGroup=config['workgroup'])
    statement_list = []
    for statement in prepared_statements['PreparedStatements']:
        statement_list.append(statement['StatementName'])
    # create prepared statement
    if name in statement_list:
        # update prepared statement
        athena_parameters = {
            'QueryStatement': query,
            'StatementName': name,
            'WorkGroup': config['workgroup'],
        }
        on_create_update = AwsSdkCall(
            action='updatePreparedStatement',
            service='Athena',
            parameters=athena_parameters,
            physical_resource_id=PhysicalResourceId.of(
                f'workgroup:{workgroup}/prepared-statement:{name}'
            ),
        )
    else:
        athena_parameters = {
            'QueryStatement': query,
            'StatementName': name,
            'WorkGroup': config['workgroup'],
        }
        on_create_update = AwsSdkCall(
            action='createPreparedStatement',
            service='Athena',
            parameters=athena_parameters,
            physical_resource_id=PhysicalResourceId.of(
                f'workgroup:{workgroup}/prepared-statement:{name}'
            ),
        )

    return on_create_update


def get_on_delete(resource):
    config = resource.get('config', {})
    name = resource['name']
    prepared_statements = client.list_prepared_statements(WorkGroup=config['workgroup'])
    statement_list = []
    for statement in prepared_statements['PreparedStatements']:
        statement_list.append(statement['StatementName'])
    # delete prepared statement
    if name in statement_list:
        # delete prepared statement
        athena_parameters = {'StatementName': name, 'WorkGroup': config['workgroup']}
        on_delete = AwsSdkCall(
            action='deletePreparedStatement',
            service='Athena',
            parameters=athena_parameters,
        )
    else:
        on_delete = None

    return on_delete


def make_athena_prepared_statement(stack, resource):
    """Makes athena prepared statement.
    Since there is no CloudFormation call for it we have to create a custom resource
    (scope, id, *, policy, function_name=None, install_latest_aws_sdk=None, log_retention=None, on_create=None, on_delete=None, on_update=None, resource_type=None, role=None, timeout=None)
    """
    # reading files/queries from config.yaml and insert variables
    """
    Example of templating
        >>> template = Template('Hello {{ name }}!')
        >>> template.render(name='John Doe')
    """
    config = resource.get('config')

    logger.info('Configuration loaded')
    if config.get('query') and config.get('query').get('file'):
        with open(config.get('query').get('file'), 'r') as f:
            query_templatized = Template(f.read())
            query = query_templatized.render(config.get('query').get('variables'))
    elif config.get('query') and config.get('query').get('query_string'):
        query_templatized = Template(config.get('query').get('query_string'))
        query = query_templatized.render(config.get('query').get('variables'))

    # custom resource policy
    policy = AwsCustomResourcePolicy.from_sdk_calls(
        resources=AwsCustomResourcePolicy.ANY_RESOURCE
    )

    # creating CDK custom resource
    prepared_statement = AwsCustomResource(
        stack,
        id=resource.get('name'),
        policy=policy,
        on_create=get_on_create_update(resource, query),
        on_update=get_on_create_update(resource, query),
        on_delete=get_on_delete(resource),
        resource_type='Custom::Athena-Prepared-Statement',
    )

    return prepared_statement
