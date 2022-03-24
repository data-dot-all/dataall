import pytest

import dataall


@pytest.fixture(scope='module')
def org1(org, user, group, tenant):
    org1 = org('testorg', user.userName, group.name)
    yield org1


@pytest.fixture(scope='module')
def env1(env, org1, user, group, tenant, module_mocker):
    module_mocker.patch('requests.post', return_value=True)
    module_mocker.patch(
        'dataall.api.Objects.Environment.resolvers.check_environment', return_value=True
    )
    env1 = env(org1, 'dev', user.userName, group.name, '111111111111', 'eu-west-1')
    yield env1


@pytest.fixture(scope='module', autouse=True)
def vpc(env1, group, client) -> dataall.db.models.Vpc:
    response = client.query(
        """
        mutation createNetwork($input:NewVpcInput){
            createNetwork(input:$input){
                vpcUri
                label
                description
                tags
                owner
                SamlGroupName
                privateSubnetIds
                privateSubnetIds
            }
        }
        """,
        input={
            'label': 'myvpc',
            'SamlGroupName': group.name,
            'tags': [group.name],
            'vpcId': 'vpc-12345678',
            'privateSubnetIds': ['sub1', 'sub2'],
            'publicSubnetIds': ['sub1', 'sub2'],
            'environmentUri': env1.environmentUri,
        },
        username='alice',
        groups=[group.name],
    )
    assert response.data.createNetwork.SamlGroupName
    assert response.data.createNetwork.label
    yield response.data.createNetwork


def test_list_networks(client, env1, db, org1, user, group, vpc):
    response = client.query(
        """
        query ListEnvironmentNetworks($environmentUri: String!,$filter:VpcFilter){
            listEnvironmentNetworks(environmentUri:$environmentUri,filter:$filter){
                count
                nodes{
                    VpcId
                    SamlGroupName
                    publicSubnetIds
                    privateSubnetIds
                    default
                }
            }
        }
        """,
        environmentUri=env1.environmentUri,
        filter=None,
        username='alice',
        groups=[group.name],
    )
    print(response)

    assert response.data.listEnvironmentNetworks.count == 2


def test_list_networks_nopermissions(client, env1, db, org1, user, group2, vpc):
    response = client.query(
        """
        query ListEnvironmentNetworks($environmentUri: String!,$filter:VpcFilter){
            listEnvironmentNetworks(environmentUri:$environmentUri,filter:$filter){
                count
                nodes{
                    VpcId
                    SamlGroupName
                    publicSubnetIds
                    privateSubnetIds
                    default
                }
            }
        }
        """,
        environmentUri=env1.environmentUri,
        filter=None,
        username='bob',
        groups=[group2.name],
    )
    assert 'UnauthorizedOperation' in response.errors[0].message


def test_get_network(client, env1, db, org1, user, group, vpc, module_mocker):
    response = client.query(
        """
        query getNetwork($vpcUri:String!){
            getNetwork(vpcUri:$vpcUri){
                vpcUri
            }
        }
        """,
        vpcUri=vpc.vpcUri,
        username=user.userName,
        groups=[group.name],
    )
    assert response.data.getNetwork.vpcUri == vpc.vpcUri


def test_delete_network(client, env1, db, org1, user, group, module_mocker, vpc):
    module_mocker.patch(
        'dataall.aws.handlers.service_handlers.Worker.queue', return_value=True
    )
    response = client.query(
        """
        mutation deleteNetwork($vpcUri:String!){
            deleteNetwork(vpcUri:$vpcUri)
        }
        """,
        vpcUri=vpc.vpcUri,
        username=user.userName,
        groups=[group.name],
    )
    assert response.data.deleteNetwork
    response = client.query(
        """
        query ListEnvironmentNetworks($environmentUri: String!,$filter:VpcFilter){
            listEnvironmentNetworks(environmentUri:$environmentUri,filter:$filter){
                count
                nodes{
                    VpcId
                    SamlGroupName
                    publicSubnetIds
                    privateSubnetIds
                    default
                }
            }
        }
        """,
        environmentUri=env1.environmentUri,
        filter=None,
        username='alice',
        groups=[group.name],
    )
    assert len(response.data.listEnvironmentNetworks['nodes']) == 1
