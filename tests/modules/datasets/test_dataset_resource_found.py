import pytest

from dataall.modules.datasets_base.db.models import Dataset
from dataall.modules.datasets.services.dataset_permissions import CREATE_DATASET


@pytest.fixture(scope='module', autouse=True)
def org1(org, user, group, tenant):
    org1 = org('testorg', user.userName, group.name)
    yield org1


@pytest.fixture(scope='module', autouse=True)
def env1(env, org1, user, group, tenant):
    env1 = env(org1, 'dev', user.userName, group.name, '111111111111', 'eu-west-1')
    yield env1


def get_env(client, env1, group):
    return client.query(
        """
        query GetEnv($environmentUri:String!){
            getEnvironment(environmentUri:$environmentUri){
                organization{
                    organizationUri
                }
                environmentUri
                label
                AwsAccountId
                region
                SamlGroupName
                owner
                warehousesEnabled
                stack{
                 EcsTaskArn
                 EcsTaskId
                }
                parameters {
                    key
                    value
                }
            }
        }
        """,
        username='alice',
        environmentUri=env1.environmentUri,
        groups=[group.name],
    )


def test_dataset_resource_found(db, client, env1, org1, group2, user, group3, group, dataset):
    response = client.query(
        """
        query listEnvironmentGroupInvitationPermissions($environmentUri:String){
            listEnvironmentGroupInvitationPermissions(environmentUri:$environmentUri){
                    permissionUri
                    name
                    type
            }
        }
        """,
        username=user.userName,
        groups=[group.name, group2.name],
        filter={},
    )

    env_permissions = [
        p.name for p in response.data.listEnvironmentGroupInvitationPermissions
    ]
    assert CREATE_DATASET in env_permissions

    response = client.query(
        """
        mutation inviteGroupOnEnvironment($input:InviteGroupOnEnvironmentInput){
            inviteGroupOnEnvironment(input:$input){
                environmentUri
            }
        }
        """,
        username='alice',
        input=dict(
            environmentUri=env1.environmentUri,
            groupUri=group2.name,
            permissions=env_permissions,
            environmentIAMRoleName='myteamrole',
        ),
        groups=[group.name, group2.name],
    )
    print(response)
    assert response.data.inviteGroupOnEnvironment

    response = client.query(
        """
        query getGroup($groupUri:String!, $environmentUri:String){
            getGroup(groupUri:$groupUri){
                environmentPermissions(environmentUri:$environmentUri){
                 name
                }
            }
        }
        """,
        username=user.userName,
        groups=[group2.name],
        groupUri=group2.name,
        environmentUri=env1.environmentUri,
    )
    env_permissions = [p.name for p in response.data.getGroup.environmentPermissions]
    assert CREATE_DATASET in env_permissions

    dataset = dataset(
        org=org1, env=env1, name='dataset1', owner='bob', group=group2.name
    )
    assert dataset.datasetUri

    response = client.query(
        """
        mutation removeGroupFromEnvironment($environmentUri: String!, $groupUri: String!){
            removeGroupFromEnvironment(environmentUri: $environmentUri, groupUri: $groupUri){
                environmentUri
            }
        }
        """,
        username='alice',
        environmentUri=env1.environmentUri,
        groupUri=group2.name,
        groups=[group.name, group2.name],
    )
    print(response)

    assert 'EnvironmentResourcesFound' in response.errors[0].message
    with db.scoped_session() as session:
        dataset = session.query(Dataset).get(dataset.datasetUri)
        session.delete(dataset)
        session.commit()

    response = client.query(
        """
        mutation removeGroupFromEnvironment($environmentUri: String!, $groupUri: String!){
            removeGroupFromEnvironment(environmentUri: $environmentUri, groupUri: $groupUri){
                environmentUri
            }
        }
        """,
        username='alice',
        environmentUri=env1.environmentUri,
        groupUri=group2.name,
        groups=[group.name, group2.name],
    )
    print(response)
    assert response.data.removeGroupFromEnvironment

