from assertpy import assert_that

from integration_tests.errors import GqlError
from integration_tests.core.vpc.queries import create_network, delete_network, list_environment_networks


def test_create_network(network1, session_id):
    assert_that(network1).contains_entry(label='testVpc1', tags=[session_id], VpcId='someId')
    assert_that(network1.vpcUri).is_not_none()


def test_create_network_unauthorized(client2, group2, session_env1, session_id):
    assert_that(create_network).raises(GqlError).when_called_with(
        client2,
        name='testVpc2',
        vpc_id='someId2',
        public_subnets=['testSubnet2'],
        environment_uri=session_env1.environmentUri,
        group=group2,
        tags=[session_id],
    ).contains('UnauthorizedOperation', 'CREATE_NETWORK', session_env1.environmentUri)


def test_create_duplicated_network_invalid(client1, group1, session_env1, session_id, network1):
    assert_that(create_network).raises(GqlError).when_called_with(
        client1,
        name='testVpcDuplicated2',
        vpc_id='someId',
        public_subnets=['testSubnet1'],
        environment_uri=session_env1.environmentUri,
        group=group1,
        tags=[session_id],
    ).contains('ResourceAlreadyExists', 'CREATE_NETWORK', 'someId')


def test_delete_network(client1, group1, session_env1, session_id):
    response = create_network(
        client1,
        name='testVpcDelete',
        vpc_id='someIdDelete',
        public_subnets=['testSubnet1'],
        environment_uri=session_env1.environmentUri,
        group=group1,
        tags=[session_id],
    )
    assert_that(response.vpcUri).is_not_none()
    response = delete_network(client1, vpc_uri=response.vpcUri)
    assert_that(response).is_true()


def test_delete_network_unauthorized(client2, network1):
    assert_that(delete_network).raises(GqlError).when_called_with(
        client2,
        vpc_uri=network1.vpcUri,
    ).contains('UnauthorizedOperation', 'DELETE_NETWORK', network1.vpcUri)


def test_list_environment_networks(client1, network1, session_env1, session_id):
    response = list_environment_networks(client1, environment_uri=session_env1.environmentUri, term=session_id)
    assert_that(response.count).is_equal_to(1)
    assert_that(response.nodes[0]).contains_entry(label='testVpc1', VpcId='someId', vpcUri=network1.vpcUri)


def test_list_environment_networks_unauthorized(client2, network1, session_env1):
    assert_that(list_environment_networks).raises(GqlError).when_called_with(
        client2,
        environment_uri=session_env1.environmentUri,
    ).contains('UnauthorizedOperation', 'LIST_ENVIRONMENT_NETWORKS', session_env1.environmentUri)
