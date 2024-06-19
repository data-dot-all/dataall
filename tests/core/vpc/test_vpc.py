import pytest

from dataall.core.vpc.db.vpc_models import Vpc


@pytest.fixture(scope='module', autouse=True)
def vpc(env_fixture, group, client) -> Vpc:
    response = client.query(
        """
        mutation createNetwork($input:NewVpcInput!){
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
            'environmentUri': env_fixture.environmentUri,
        },
        username='alice',
        groups=[group.name],
    )
    assert response.data.createNetwork.SamlGroupName
    assert response.data.createNetwork.label
    yield response.data.createNetwork


def test_list_networks(client, env_fixture, db, user, group, vpc):
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
        environmentUri=env_fixture.environmentUri,
        filter=None,
        username='alice',
        groups=[group.name],
    )
    print(response)

    assert response.data.listEnvironmentNetworks.count == 1


def test_list_networks_nopermissions(client, env_fixture, db, user, group2, vpc):
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
        environmentUri=env_fixture.environmentUri,
        filter=None,
        username='bob',
        groups=[group2.name],
    )
    assert 'UnauthorizedOperation' in response.errors[0].message


def test_delete_network(client, env_fixture, db, user, group, module_mocker, vpc):
    response = client.query(
        """
        mutation deleteNetwork($vpcUri:String!){
            deleteNetwork(vpcUri:$vpcUri)
        }
        """,
        vpcUri=vpc.vpcUri,
        username=user.username,
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
        environmentUri=env_fixture.environmentUri,
        filter=None,
        username='alice',
        groups=[group.name],
    )
    assert len(response.data.listEnvironmentNetworks['nodes']) == 0
