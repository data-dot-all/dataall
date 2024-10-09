import logging

import pytest

from integration_tests.client import GqlError
from integration_tests.modules.notebooks.queries import (
    create_sagemaker_notebook,
    get_sagemaker_notebook,
    delete_sagemaker_notebook,
    list_sagemaker_notebooks,
)
from integration_tests.core.stack.utils import check_stack_ready, wait_stack_delete_complete
from integration_tests.core.environment.utils import set_env_params

from integration_tests.modules.notebooks.aws_clients import VpcClient

log = logging.getLogger(__name__)


def create_notebook(client, group, env_uri, vpc_id, subnet_id, tags=[], name='TestNotebook'):
    notebook = create_sagemaker_notebook(
        client=client,
        name=name,
        group=group,
        environmentUri=env_uri,
        VpcId=vpc_id,
        SubnetId=subnet_id,
        tags=tags,
    )
    check_stack_ready(
        client=client,
        env_uri=env_uri,
        stack_uri=notebook.stack.stackUri,
        target_uri=notebook.notebookUri,
        target_type='notebook',
    )
    return get_sagemaker_notebook(client, notebook.notebookUri)


def delete_notebook(client, env_uri, notebook):
    check_stack_ready(
        client=client,
        env_uri=env_uri,
        stack_uri=notebook.stack.stackUri,
        target_uri=notebook.notebookUri,
        target_type='notebook',
    )
    try:
        return delete_sagemaker_notebook(client, notebook.notebookUri)
    except GqlError:
        log.exception('unexpected error when deleting environment')
        return False


"""
Session envs persist accross the duration of the whole integ test suite and are meant to make the test suite run faster (env creation takes ~2 mins).
For this reason they must stay immutable as changes to them will affect the rest of the tests.
"""


@pytest.fixture(scope='session')
def session_notebook1(client1, group1, session_env1, session_id, session_env1_aws_client):
    resource_name = 'sessionnotebook1'
    notebook = None
    try:
        set_env_params(client1, session_env1, notebooksEnabled='true')
        vpc_client = VpcClient(session=session_env1_aws_client, region=session_env1['region'])
        vpc_id = vpc_client.create_vpc(vpc_name=resource_name, cidr='172.31.0.0/26')
        subnet_id = vpc_client.create_subnet(vpc_id=vpc_id, subnet_name=resource_name, cidr='172.31.0.0/28')
        notebook = create_notebook(
            client1,
            group=group1,
            env_uri=session_env1['environmentUri'],
            tags=[session_id],
            vpc_id=vpc_id,
            subnet_id=subnet_id,
        )
        yield notebook
    finally:
        if notebook:
            delete_notebook(client1, session_env1['environmentUri'], notebook)
            wait_stack_delete_complete(
                session_env1_aws_client.client('cloudformation', region_name=session_env1['region']),
                notebook.stack.name,
            )

        vpc_client = VpcClient(session=session_env1_aws_client, region=session_env1['region'])
        vpc_client.delete_subnet_by_name(resource_name)
        vpc_client.delete_vpc_by_name(resource_name)


"""
Temp envs will be created and deleted per test, use with caution as they might increase the runtime of the test suite.
They are suitable to test env mutations.
"""


@pytest.fixture(scope='function')
def temp_notebook1(client1, group1, session_env1, session_id, session_env1_aws_client):
    resource_name = 'tempnotebook1'
    notebook = None
    try:
        vpc_client = VpcClient(session=session_env1_aws_client, region=session_env1['region'])
        vpc_id = vpc_client.create_vpc(vpc_name=resource_name, cidr='172.31.0.0/26')
        subnet_id = vpc_client.create_subnet(vpc_id=vpc_id, subnet_name=resource_name, cidr='172.31.0.0/28')

        notebook = create_notebook(
            client1,
            group=group1,
            env_uri=session_env1['environmentUri'],
            tags=[session_id],
            vpc_id=vpc_id,
            subnet_id=subnet_id,
        )
        yield notebook
    finally:
        if notebook:
            delete_notebook(client1, session_env1['environmentUri'], notebook)
        vpc_client = VpcClient(session=session_env1_aws_client, region=session_env1['region'])
        vpc_client.delete_subnet_by_name(resource_name)
        vpc_client.delete_vpc_by_name(resource_name)


"""
Persistent environments must always be present (if not i.e first run they will be created but won't be removed).
They are suitable for testing backwards compatibility. 
"""


def get_or_create_persistent_notebook(resource_name, client, group, env, session):
    notebooks = list_sagemaker_notebooks(client, term=resource_name).nodes
    if notebooks:
        return notebooks[0]
    else:
        vpc_client = VpcClient(session=session, region=env['region'])

        vpc_id = (
            vpc_client.get_vpc_id_by_name(resource_name)
            if vpc_client.get_vpc_id_by_name(resource_name)
            else vpc_client.create_vpc(vpc_name=resource_name, cidr='172.31.1.0/26')
        )

        subnet_id = (
            vpc_client.get_subnet_id_by_name(resource_name)
            if vpc_client.get_subnet_id_by_name(resource_name)
            else vpc_client.create_subnet(vpc_id=vpc_id, subnet_name=resource_name, cidr='172.31.1.0/28')
        )

        notebook = create_notebook(
            client,
            group=group,
            env_uri=env['environmentUri'],
            tags=[resource_name],
            vpc_id=vpc_id,
            subnet_id=subnet_id,
            name=resource_name,
        )
        if notebook.stack.status in ['CREATE_COMPLETE', 'UPDATE_COMPLETE']:
            return notebook
        else:
            delete_notebook(client, env['environmentUri'], notebook)
            raise RuntimeError(f'failed to create {resource_name=} {notebook=}')


@pytest.fixture(scope='session')
def persistent_notebook1(client1, group1, persistent_env1, persistent_env1_aws_client):
    set_env_params(client1, persistent_env1, notebooksEnabled='true')
    return get_or_create_persistent_notebook(
        'persistent_notebook1', client1, group1, persistent_env1, persistent_env1_aws_client
    )
