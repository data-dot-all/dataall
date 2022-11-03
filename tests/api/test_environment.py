import pytest

import dataall
from dataall.db import permissions


@pytest.fixture(scope='module', autouse=True)
def org1(org, user, group, tenant):
    org1 = org('testorg', user.userName, group.name)
    yield org1


@pytest.fixture(scope='module', autouse=True)
def env1(env, org1, user, group, tenant, module_mocker):
    module_mocker.patch('requests.post', return_value=True)
    module_mocker.patch(
        'dataall.api.Objects.Environment.resolvers.check_environment', return_value=True
    )
    env1 = env(org1, 'dev', user.userName, group.name, '111111111111', 'eu-west-1')
    yield env1


def test_get_environment(client, org1, env1, group):
    response = client.query(
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
                dashboardsEnabled
                notebooksEnabled
                mlStudiosEnabled
                pipelinesEnabled
                warehousesEnabled
                stack{
                 EcsTaskArn
                 EcsTaskId
                }
            }
        }
        """,
        username='alice',
        environmentUri=env1.environmentUri,
        groups=[group.name],
    )
    assert (
        response.data.getEnvironment.organization.organizationUri
        == org1.organizationUri
    )
    assert response.data.getEnvironment.owner == 'alice'
    assert response.data.getEnvironment.AwsAccountId == env1.AwsAccountId
    assert response.data.getEnvironment.dashboardsEnabled
    assert response.data.getEnvironment.notebooksEnabled
    assert response.data.getEnvironment.mlStudiosEnabled
    assert response.data.getEnvironment.pipelinesEnabled
    assert response.data.getEnvironment.warehousesEnabled


def test_get_environment_object_not_found(client, org1, env1, group):
    response = client.query(
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
            }
        }
        """,
        username='alice',
        environmentUri='doesnotexist',
        groups=[group.name],
    )
    assert 'UnauthorizedOperation' in response.errors[0].message


def test_update_env(client, org1, env1, group):
    response = client.query(
        """
        mutation UpdateEnv($environmentUri:String!,$input:ModifyEnvironmentInput){
            updateEnvironment(environmentUri:$environmentUri,input:$input){
                organization{
                    organizationUri
                }
                label
                AwsAccountId
                region
                SamlGroupName
                owner
                tags
                resourcePrefix
                dashboardsEnabled
                notebooksEnabled
                mlStudiosEnabled
                pipelinesEnabled
                warehousesEnabled

            }
        }
        """,
        username='alice',
        environmentUri=env1.environmentUri,
        input={
            'label': 'DEV',
            'tags': ['test', 'env'],
            'dashboardsEnabled': False,
            'notebooksEnabled': False,
            'mlStudiosEnabled': False,
            'pipelinesEnabled': False,
            'warehousesEnabled': False,
            'resourcePrefix': 'customer-prefix_AZ390 ',
        },
        groups=[group.name],
    )
    assert 'InvalidInput' in response.errors[0].message

    response = client.query(
        """
        mutation UpdateEnv($environmentUri:String!,$input:ModifyEnvironmentInput){
            updateEnvironment(environmentUri:$environmentUri,input:$input){
                organization{
                    organizationUri
                }
                label
                AwsAccountId
                region
                SamlGroupName
                owner
                tags
                resourcePrefix
                dashboardsEnabled
                notebooksEnabled
                mlStudiosEnabled
                pipelinesEnabled
                warehousesEnabled

            }
        }
        """,
        username='alice',
        environmentUri=env1.environmentUri,
        input={
            'label': 'DEV',
            'tags': ['test', 'env'],
            'dashboardsEnabled': False,
            'notebooksEnabled': False,
            'mlStudiosEnabled': False,
            'pipelinesEnabled': False,
            'warehousesEnabled': False,
            'resourcePrefix': 'customer-prefix',
        },
        groups=[group.name],
    )
    print(response)
    assert (
        response.data.updateEnvironment.organization.organizationUri
        == org1.organizationUri
    )
    assert response.data.updateEnvironment.owner == 'alice'
    assert response.data.updateEnvironment.AwsAccountId == env1.AwsAccountId
    assert response.data.updateEnvironment.label == 'DEV'
    assert str(response.data.updateEnvironment.tags) == str(['test', 'env'])
    assert not response.data.updateEnvironment.dashboardsEnabled
    assert not response.data.updateEnvironment.notebooksEnabled
    assert not response.data.updateEnvironment.mlStudiosEnabled
    assert not response.data.updateEnvironment.pipelinesEnabled
    assert not response.data.updateEnvironment.warehousesEnabled
    assert response.data.updateEnvironment.resourcePrefix == 'customer-prefix'


def test_unauthorized_update(client, org1, env1):
    response = client.query(
        """
        mutation UpdateEnv($environmentUri:String!,$input:ModifyEnvironmentInput){
            updateEnvironment(environmentUri:$environmentUri,input:$input){
                organization{
                    organizationUri
                }
                label
                AwsAccountId
                region
                SamlGroupName
                owner
                tags
            }
        }
        """,
        username='bob',
        environmentUri=env1.environmentUri,
        input={'label': 'DEV', 'tags': ['test', 'env']},
    )
    assert 'UnauthorizedOperation' in response.errors[0].message


def test_list_environments_no_filter(org1, env1, client, group):
    response = client.query(
        """
    query ListEnvironments($filter:EnvironmentFilter){
        listEnvironments(filter:$filter){
            count
            nodes{
                environmentUri
                owner
                name
                userRoleInEnvironment
                label
                AwsAccountId
                region
            }
        }
    }
    """,
        username='alice',
        groups=[group.name],
    )
    print(response)

    assert response.data.listEnvironments.count == 1

    response = client.query(
        """
        query ListEnvironmentNetworks($environmentUri: String!,$filter:VpcFilter){
            listEnvironmentNetworks(environmentUri:$environmentUri,filter:$filter){
                count
                nodes{
                    VpcId
                    SamlGroupName
                }
            }
        }
        """,
        environmentUri=env1.environmentUri,
        username='alice',
        groups=[group.name],
    )
    print(response)

    assert response.data.listEnvironmentNetworks.count == 1


def test_list_environment_role_filter_as_creator(org1, env1, client, group):
    response = client.query(
        """
    query ListEnvironments($filter:EnvironmentFilter){
        listEnvironments(filter:$filter){
            count
            nodes{
                environmentUri
                name
                owner
                label
                AwsAccountId
                region
            }
        }
    }
    """,
        username='alice',
        groups=[group.name],
    )
    print('--->', response)

    assert response.data.listEnvironments.count == 1


def test_list_environment_role_filter_as_admin(db, client, org1, env1, user, group):
    response = client.query(
        """
        query ListEnvironments($filter:EnvironmentFilter){
            listEnvironments(filter:$filter){
                count
                nodes{
                    environmentUri
                    name
                    owner
                    label
                    AwsAccountId
                    region
                }
            }
        }
        """,
        username=user.userName,
        groups=[group.name],
        filter={'roles': [dataall.api.constants.EnvironmentPermission.Invited.name]},
    )

    assert response.data.listEnvironments.count == 1


def test_paging(db, client, org1, env1, user, group):
    for i in range(1, 30):
        with db.scoped_session() as session:
            env = dataall.db.models.Environment(
                organizationUri=org1.organizationUri,
                AwsAccountId=f'12345678901+{i}',
                region='eu-west-1',
                label='org',
                owner=user.userName,
                tags=[],
                description='desc',
                SamlGroupName=group.name,
                EnvironmentDefaultIAMRoleName='EnvRole',
                EnvironmentDefaultIAMRoleArn='arn:aws::123456789012:role/EnvRole/GlueJobSessionRunner',
                CDKRoleArn='arn:aws::123456789012:role/EnvRole',
                userRoleInEnvironment='999',
            )
            session.add(env)
            session.commit()

    hasNext = True
    nb_iter = 0
    page = 1
    max_iter = 10
    first_id = None
    while hasNext and nb_iter < max_iter:
        response = client.query(
            """
            query LE($filter:EnvironmentFilter){
                listEnvironments(filter:$filter){
                    count
                    page
                    pageSize
                    hasNext
                    hasPrevious
                    nodes{
                        environmentUri
                    }
                }
            }
            """,
            username=user.userName,
            filter={'page': page, 'pageSize': 5},
            groups=[group.name],
        )
        assert len(response.data.listEnvironments.nodes) == 5
        hasNext = response.data.listEnvironments.hasNext
        nb_iter = nb_iter + 1
        page += 1
        if page > 1:
            assert first_id != response.data.listEnvironments.nodes[0].environmentUri
        first_id = response.data.listEnvironments.nodes[0].environmentUri


def test_group_invitation(db, client, env1, org1, group2, user, group3, group, dataset):
    response = client.query(
        """
        query listResourcePermissions($filter:ResourcePermissionFilter){
            listResourcePermissions(filter:$filter){
                count
                nodes{
                    permissionUri
                    name
                    type
                }
            }
        }
        """,
        username=user.userName,
        groups=[group.name, group2.name],
        filter={},
    )

    assert response.data.listResourcePermissions.count > 1

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
    assert permissions.CREATE_DATASET in env_permissions

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
    assert permissions.CREATE_DATASET in env_permissions

    response = client.query(
        """
        mutation updateGroupEnvironmentPermissions($input:InviteGroupOnEnvironmentInput!){
            updateGroupEnvironmentPermissions(input:$input){
                environmentUri
            }
        }
        """,
        username='alice',
        input=dict(
            environmentUri=env1.environmentUri,
            groupUri=group2.name,
            permissions=env_permissions,
        ),
        groups=[group.name, group2.name],
    )
    print(response)
    assert response.data.updateGroupEnvironmentPermissions
    response = client.query(
        """
        query listEnvironmentInvitedGroups($environmentUri: String!, $filter:GroupFilter){
            listEnvironmentInvitedGroups(environmentUri:$environmentUri, filter:$filter){
                count
                nodes{
                    groupUri
                    name
                }
            }
        }
        """,
        username=user.userName,
        groups=[group.name, group2.name],
        environmentUri=env1.environmentUri,
        filter={},
    )

    assert response.data.listEnvironmentInvitedGroups.count == 1

    response = client.query(
        """
        query listEnvironmentGroups($environmentUri: String!, $filter:GroupFilter){
            listEnvironmentGroups(environmentUri:$environmentUri, filter:$filter){
                count
                nodes{
                    groupUri
                    name
                    environmentIAMRoleName
                }
            }
        }
        """,
        username=user.userName,
        groups=[group.name, group2.name],
        environmentUri=env1.environmentUri,
        filter={},
    )

    assert response.data.listEnvironmentGroups.count == 2
    assert 'myteamrole' in [
        g.environmentIAMRoleName for g in response.data.listEnvironmentGroups.nodes
    ]

    response = client.query(
        """
        query listEnvironmentGroups($environmentUri: String!, $filter:GroupFilter){
            listEnvironmentGroups(environmentUri:$environmentUri, filter:$filter){
                count
                nodes{
                    groupUri
                    name
                }
            }
        }
        """,
        username=user.userName,
        groups=[group.name],
        environmentUri=env1.environmentUri,
        filter={},
    )

    assert response.data.listEnvironmentGroups.count == 1

    response = client.query(
        """
        query listAllEnvironmentGroups($environmentUri: String!, $filter:GroupFilter){
            listAllEnvironmentGroups(environmentUri:$environmentUri, filter:$filter){
                count
                nodes{
                    groupUri
                    name
                }
            }
        }
        """,
        username=user.userName,
        groups=[group.name],
        environmentUri=env1.environmentUri,
        filter={},
    )

    assert response.data.listAllEnvironmentGroups.count == 2

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
        dataset = session.query(dataall.db.models.Dataset).get(dataset.datasetUri)
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

    response = client.query(
        """
        query listEnvironmentInvitedGroups($environmentUri: String!, $filter:GroupFilter){
            listEnvironmentInvitedGroups(environmentUri:$environmentUri, filter:$filter){
                count
                nodes{
                    groupUri
                    name
                }
            }
        }
        """,
        username=user.userName,
        groups=[group.name, group2.name],
        environmentUri=env1.environmentUri,
        filter={},
    )

    assert response.data.listEnvironmentInvitedGroups.count == 0

    response = client.query(
        """
        query listEnvironmentGroups($environmentUri: String!, $filter:GroupFilter){
            listEnvironmentGroups(environmentUri:$environmentUri, filter:$filter){
                count
                nodes{
                    groupUri
                    name
                }
            }
        }
        """,
        username=user.userName,
        groups=[group.name, group2.name],
        environmentUri=env1.environmentUri,
        filter={},
    )

    assert response.data.listEnvironmentGroups.count == 1

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
            groupUri=group3.name,
            permissions=env_permissions,
        ),
        groups=[group.name, group3.name],
    )
    print(response)
    assert response.data.inviteGroupOnEnvironment

    response = client.query(
        """
        query listEnvironmentGroups($environmentUri: String!, $filter:GroupFilter){
            listEnvironmentGroups(environmentUri:$environmentUri, filter:$filter){
                count
                nodes{
                    groupUri
                    name
                    environmentIAMRoleName
                }
            }
        }
        """,
        username=user.userName,
        groups=[group.name, group2.name, group3.name],
        environmentUri=env1.environmentUri,
        filter={},
    )
    assert 'myteamrole' not in [
        g.environmentIAMRoleName for g in response.data.listEnvironmentGroups.nodes
    ]


def test_archive_env(client, org1, env1, group, group2):
    response = client.query(
        """
        mutation deleteEnvironment($environmentUri:String!, $deleteFromAWS:Boolean!){
            deleteEnvironment(environmentUri:$environmentUri, deleteFromAWS:$deleteFromAWS)
        }
        """,
        username='alice',
        groups=[group.name, group2.name],
        environmentUri=env1.environmentUri,
        deleteFromAWS=True,
    )
    print(response)
    assert response.data.deleteEnvironment


def test_create_environment(db, client, org1, env1, user, group):
    response = client.query(
        """mutation CreateEnv($input:NewEnvironmentInput){
            createEnvironment(input:$input){
                organization{
                    organizationUri
                }
                environmentUri
                label
                AwsAccountId
                SamlGroupName
                region
                name
                owner
                EnvironmentDefaultIAMRoleName
                EnvironmentDefaultIAMRoleImported
                dashboardsEnabled
                resourcePrefix
                networks{
                 VpcId
                 region
                 privateSubnetIds
                 publicSubnetIds
                 default
                }
            }
        }""",
        username=user.userName,
        groups=[group.name],
        input={
            'label': f'dev',
            'description': f'test',
            'EnvironmentDefaultIAMRoleName': 'myOwnIamRole',
            'organizationUri': org1.organizationUri,
            'AwsAccountId': env1.AwsAccountId,
            'tags': ['a', 'b', 'c'],
            'region': f'{env1.region}',
            'SamlGroupName': group.name,
            'vpcId': 'vpc-1234567',
            'privateSubnetIds': 'subnet-1',
            'publicSubnetIds': 'subnet-21',
            'dashboardsEnabled': True,
            'resourcePrefix': 'customer-prefix',
        },
    )
    assert response.data.createEnvironment.dashboardsEnabled
    assert response.data.createEnvironment.networks
    assert (
        response.data.createEnvironment.EnvironmentDefaultIAMRoleName == 'myOwnIamRole'
    )
    assert response.data.createEnvironment.EnvironmentDefaultIAMRoleImported
    assert response.data.createEnvironment.resourcePrefix == 'customer-prefix'
    for vpc in response.data.createEnvironment.networks:
        assert vpc.privateSubnetIds
        assert vpc.publicSubnetIds
        assert vpc.default

    with db.scoped_session() as session:
        env = dataall.db.api.Environment.get_environment_by_uri(
            session, response.data.createEnvironment.environmentUri
        )
        session.delete(env)
        session.commit()
