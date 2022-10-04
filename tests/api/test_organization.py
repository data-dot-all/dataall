import dataall
import pytest


@pytest.fixture(scope='module', autouse=True)
def org1(org, user, group, tenant):
    org1 = org('testorg', user.userName, group.name)
    yield org1


@pytest.fixture(scope='module', autouse=True)
def org2(org, user2, group2, tenant):
    org2 = org('anothertestorg', user2.userName, group2.name)
    yield org2


@pytest.fixture(scope='module', autouse=True)
def env_dev(env, org2, user2, group2, tenant, module_mocker):
    module_mocker.patch('requests.post', return_value=True)
    module_mocker.patch('dataall.api.Objects.Environment.resolvers.check_environment', return_value=True)
    env2 = env(org2, 'dev', user2.userName, group2.name, '222222222222', 'eu-west-1', 'description')
    yield env2


@pytest.fixture(scope='module', autouse=True)
def env_other(env, org2, user2, group2, tenant, module_mocker):
    module_mocker.patch('requests.post', return_value=True)
    module_mocker.patch('dataall.api.Objects.Environment.resolvers.check_environment', return_value=True)
    env2 = env(org2, 'other', user2.userName, group2.name, '222222222222', 'eu-west-1')
    yield env2


@pytest.fixture(scope='module', autouse=True)
def env_prod(env, org2, user2, group2, tenant, module_mocker):
    module_mocker.patch('requests.post', return_value=True)
    module_mocker.patch('dataall.api.Objects.Environment.resolvers.check_environment', return_value=True)
    env2 = env(org2, 'prod', user2.userName, group2.name, '111111111111', 'eu-west-1', 'description')
    yield env2


def test_get_org(client, org1, group):
    response = client.query(
        """
        query GetOrg($organizationUri:String!){
            getOrganization(organizationUri:$organizationUri){
                organizationUri
                label
                name
                owner
                SamlGroupName
                userRoleInOrganization
                stats{
                    environments
                    groups
                }
            }
        }
        """,
        username='alice',
        organizationUri=org1.organizationUri,
        groups=[group.name],
    )

    assert response.data.getOrganization.organizationUri == org1.organizationUri
    assert response.data.getOrganization.owner == 'alice'
    assert response.data.getOrganization.SamlGroupName == group.name
    assert response.data.getOrganization.userRoleInOrganization == 'Owner'
    assert response.data.getOrganization.stats.groups == 0


def test_update_org(client, org1, group):
    response = client.query(
        """
            mutation UpdateOrg($organizationUri:String!,$input:ModifyOrganizationInput){
                 updateOrganization(organizationUri:$organizationUri,input:$input){
                    label
                    owner
                    SamlGroupName
                }
            }
        """,
        username='alice',
        groups=[group.name],
        organizationUri=org1.organizationUri,
        input={'label': 'newlabel'},
    )

    assert response.data.updateOrganization.owner == 'alice'
    assert response.data.updateOrganization.SamlGroupName == group.name
    assert response.data.updateOrganization.label == 'newlabel'


def test_update_org_unauthorized(client, org1, group2):
    response = client.query(
        """
            mutation UpdateOrg($organizationUri:String!,$input:ModifyOrganizationInput){
                 updateOrganization(organizationUri:$organizationUri,input:$input){
                    label
                    owner
                    SamlGroupName
                }
            }
        """,
        username='bob',
        groups=[group2.name],
        organizationUri=org1.organizationUri,
        input={'label': 'newlabel'},
    )

    assert 'Unauthorized' in response.errors[0].message


def test_update_org_authorized_admins(client, org1, group):
    response = client.query(
        """
            mutation UpdateOrg($organizationUri:String!,$input:ModifyOrganizationInput){
                 updateOrganization(organizationUri:$organizationUri,input:$input){
                    label
                    owner
                    SamlGroupName
                }
            }
        """,
        username='steve',
        groups=[group.name],
        organizationUri=org1.organizationUri,
        input={'label': 'otherlabel'},
    )

    assert response.data.updateOrganization.label == 'otherlabel'


def test_list_organizations_alice(client, org1, group):
    response = client.query(
        """ query ListOrgs{
            listOrganizations{
                count
                nodes{
                    organizationUri
                    SamlGroupName
                }
            }
        }""",
        'alice',
        [group.name],
    )

    assert response.data.listOrganizations.count == 1
    assert response.data.listOrganizations.nodes[0].organizationUri == org1.organizationUri


def test_list_organizations_admin(client, org1, group):
    response = client.query(
        """ query ListOrgs{
            listOrganizations{
                count
                nodes{
                    organizationUri
                    SamlGroupName
                    userRoleInOrganization
                }
            }
        }""",
        'steve',
        [group.name],
    )
    print(response)
    assert response.data.listOrganizations.count == 1
    assert response.data.listOrganizations.nodes[0].organizationUri == org1.organizationUri


def test_list_organizations_anyone(client, org1):
    response = client.query(
        """ query ListOrgs($filter:OrganizationFilter){
            listOrganizations(filter:$filter){
                count
                nodes{
                    organizationUri
                    SamlGroupName
                }
            }
        }""",
        'tom',
        ['all'],
        filter={'roles': [dataall.api.constants.OrganisationUserRole.Member.name]},
    )
    print(response)
    assert response.data.listOrganizations.count == 0


def test_group_invitation(db, client, org1, group2, user, group3, group, dataset, env, module_mocker):
    response = client.query(
        """
        mutation inviteGroupToOrganization($input:InviteGroupToOrganizationInput){
            inviteGroupToOrganization(input:$input){
                organizationUri
            }
        }
        """,
        username='alice',
        input=dict(
            organizationUri=org1.organizationUri,
            groupUri=group2.name,
        ),
        groups=[group.name, group2.name],
    )
    print(response)
    assert response.data.inviteGroupToOrganization

    response = client.query(
        """
        query GetOrg($organizationUri:String!){
            getOrganization(organizationUri:$organizationUri){
                userRoleInOrganization
                stats{
                    environments
                    groups
                }
            }
        }
        """,
        username='bob',
        organizationUri=org1.organizationUri,
        groups=[group2.name],
    )
    assert response.data.getOrganization.userRoleInOrganization == 'Invited'
    assert response.data.getOrganization.stats.groups == 1

    response = client.query(
        """
        query listOrganizationInvitedGroups($organizationUri: String!, $filter:GroupFilter){
            listOrganizationInvitedGroups(organizationUri:$organizationUri, filter:$filter){
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
        organizationUri=org1.organizationUri,
        filter={},
    )

    assert response.data.listOrganizationInvitedGroups.count == 1

    response = client.query(
        """
        query listOrganizationNotInvitedGroups($organizationUri: String!, $filter:GroupFilter){
            listOrganizationNotInvitedGroups(organizationUri:$organizationUri, filter:$filter){
                count
                nodes{
                    groupUri
                    name
                }
            }
        }
        """,
        username=user.userName,
        groups=[group.name, group2.name, group3.name],
        organizationUri=org1.organizationUri,
        filter={},
    )

    assert response.data.listOrganizationNotInvitedGroups.count == 1

    response = client.query(
        """
        query listOrganizationGroups($organizationUri: String!, $filter:GroupFilter){
            listOrganizationGroups(organizationUri:$organizationUri, filter:$filter){
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
        organizationUri=org1.organizationUri,
        filter={},
    )

    assert response.data.listOrganizationGroups.count == 2

    module_mocker.patch('requests.post', return_value=True)
    module_mocker.patch('dataall.api.Objects.Environment.resolvers.check_environment', return_value=True)
    env2 = env(org1, 'devg2', user.userName, group2.name, '111111111112', 'eu-west-1')
    assert env2.environmentUri

    response = client.query(
        """
        mutation removeGroupFromOrganization($organizationUri: String!, $groupUri: String!){
            removeGroupFromOrganization(organizationUri: $organizationUri, groupUri: $groupUri){
                organizationUri
            }
        }
        """,
        username='alice',
        organizationUri=org1.organizationUri,
        groupUri=group2.name,
        groups=[group.name, group2.name],
    )
    print(response)

    assert 'OrganizationResourcesFound' in response.errors[0].message
    with db.scoped_session() as session:
        dataset = session.query(dataall.db.models.Environment).get(env2.environmentUri)
        session.delete(dataset)
        session.commit()

    response = client.query(
        """
        mutation removeGroupFromOrganization($organizationUri: String!, $groupUri: String!){
            removeGroupFromOrganization(organizationUri: $organizationUri, groupUri: $groupUri){
                organizationUri
            }
        }
        """,
        username='alice',
        organizationUri=org1.organizationUri,
        groupUri=group2.name,
        groups=[group.name, group2.name],
    )
    print(response)
    assert response.data.removeGroupFromOrganization

    response = client.query(
        """
        query listOrganizationInvitedGroups($organizationUri: String!, $filter:GroupFilter){
            listOrganizationInvitedGroups(organizationUri:$organizationUri, filter:$filter){
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
        organizationUri=org1.organizationUri,
        filter={},
    )

    assert response.data.listOrganizationInvitedGroups.count == 0

    response = client.query(
        """
        query listOrganizationNotInvitedGroups($organizationUri: String!, $filter:GroupFilter){
            listOrganizationNotInvitedGroups(organizationUri:$organizationUri, filter:$filter){
                count
                nodes{
                    groupUri
                    name
                }
            }
        }
        """,
        username=user.userName,
        groups=[group.name, group2.name, group3.name],
        organizationUri=org1.organizationUri,
        filter={},
    )

    assert response.data.listOrganizationNotInvitedGroups.count == 2

    response = client.query(
        """
        query listOrganizationGroups($organizationUri: String!, $filter:GroupFilter){
            listOrganizationGroups(organizationUri:$organizationUri, filter:$filter){
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
        organizationUri=org1.organizationUri,
        filter={},
    )

    assert response.data.listOrganizationGroups.count == 1


def test_archive_org(client, org1, group, group2):
    response = client.query(
        """
        mutation archiveOrganization($organizationUri:String!){
            archiveOrganization(organizationUri:$organizationUri)
        }
        """,
        username='alice',
        groups=[group.name, group2.name],
        organizationUri=org1.organizationUri,
    )
    print(response)
    assert response.data.archiveOrganization


def test_list_organization_environments(org2, client, group2):
    response = client.query(
        """
        query GetOrg($organizationUri:String!, $filter: EnvironmentFilter){
            getOrganization(organizationUri:$organizationUri){
                environments(filter: $filter) {
                    count
                    nodes {
                        label
                        description
                    }
                }
            }
        }
        """,
        username='alice',
        organizationUri=org2.organizationUri,
        groups=[group2.name],
        filter={'term': ''},
    )

    assert response.data.getOrganization.environments.count == 3


def test_list_organization_environments_filter_by_label(org2, env_other, client, group2):
    response = client.query(
        """
        query GetOrg($organizationUri:String!, $filter: EnvironmentFilter){
            getOrganization(organizationUri:$organizationUri){
                environments(filter: $filter) {
                    count
                    nodes {
                        label
                        description
                    }
                }
            }
        }
        """,
        username='alice',
        organizationUri=org2.organizationUri,
        groups=[group2.name],
        filter={'term': 'other'},
    )

    assert response.data.getOrganization.environments.count == 1
    assert response.data.getOrganization.environments.nodes[0].label == env_other.label


def test_list_organization_environments_filter_by_desc(org2, env_dev, env_prod, client, group2):
    response = client.query(
        """
        query GetOrg($organizationUri:String!, $filter: EnvironmentFilter){
            getOrganization(organizationUri:$organizationUri){
                environments(filter: $filter) {
                    count
                    nodes {
                        label
                        description
                    }
                }
            }
        }
        """,
        username='alice',
        organizationUri=org2.organizationUri,
        groups=[group2.name],
        filter={'term': 'description'},
    )

    assert response.data.getOrganization.environments.count == 2
    envs = set(map(lambda n: n.label, response.data.getOrganization.environments.nodes))
    assert env_dev.label in envs
    assert env_prod.label in envs
