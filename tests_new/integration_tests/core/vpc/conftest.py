import pytest
from integration_tests.core.vpc.queries import create_network, delete_network


@pytest.fixture(scope='function')
def network1(client1, group1, session_env1, session_id):
    network = None
    try:
        network = create_network(
            client1,
            name='testVpc1',
            vpc_id='someId',
            public_subnets=['testSubnet1'],
            environment_uri=session_env1.environmentUri,
            group=group1,
            tags=[session_id],
        )
        yield network
    finally:
        if network:
            delete_network(client1, vpc_uri=network.vpcUri)
