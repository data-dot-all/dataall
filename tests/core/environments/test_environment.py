from dataall.core.environment.api.enums import EnvironmentPermission
from dataall.core.environment.db.environment_models import Environment
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.permissions.services.environment_permissions import (
    REMOVE_ENVIRONMENT_CONSUMPTION_ROLE,
)
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService


def get_env(client, env_fixture, group):
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
        environmentUri=env_fixture.environmentUri,
        groups=[group.name],
    )


def test_create_environment_with_external_group(db, client, org_fixture, user, group, not_in_org_group):
    response = client.query(
        """mutation CreateEnv($input:NewEnvironmentInput!){
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
        username=user.username,
        groups=[group.name, not_in_org_group.name],
        input={
            'label': f'dev',
            'description': f'test',
            'EnvironmentDefaultIAMRoleArn': 'arn:aws:iam::444444444444:role/myOwnIamRole',
            'organizationUri': org_fixture.organizationUri,
            'AwsAccountId': '444444444444',
            'tags': ['a', 'b', 'c'],
            'region': 'eu-west-1',
            'SamlGroupName': not_in_org_group.name,
            'resourcePrefix': 'customer-prefix',
        },
    )

    assert 'is not a member of the organization' in response.errors[0].message


def test_create_environment_invalid_account_region(client, org_fixture, env_fixture, group):
    response = client.query(
        """mutation CreateEnv($input:NewEnvironmentInput!){
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
                    parameters {
                        key
                        value
                    }
                }
            }""",
        username='alice',
        groups=[group.name],
        input={
            'label': 'invalid',
            'description': 'invalid environment',
            'organizationUri': org_fixture.organizationUri,
            'AwsAccountId': env_fixture.AwsAccountId,
            'tags': ['a', 'b', 'c'],
            'region': env_fixture.region,
            'SamlGroupName': group.name,
            'parameters': [{'key': k, 'value': v} for k, v in {'dashboardsEnabled': 'true'}.items()],
        },
    )
    assert 'InvalidInput' in response.errors[0].message


def test_get_environment(client, org_fixture, env_fixture, group):
    response = get_env(client, env_fixture, group)
    assert response.data.getEnvironment.organization.organizationUri == org_fixture.organizationUri
    body = response.data.getEnvironment
    assert body.owner == 'alice'
    assert body.AwsAccountId == env_fixture.AwsAccountId

    params = {p.key: p.value for p in body.parameters}
    assert params['dashboardsEnabled'] == 'true'


def test_get_environment_object_not_found(client, org_fixture, env_fixture, group):
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


def test_update_env(client, org_fixture, env_fixture, group):
    query = """
        mutation UpdateEnv($environmentUri:String!,$input:ModifyEnvironmentInput!){
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
                parameters {
                    key
                    value
                }
            }
        }
    """

    response = client.query(
        query,
        username='alice',
        environmentUri=env_fixture.environmentUri,
        input={
            'label': 'DEV',
            'tags': ['test', 'env'],
            'parameters': [{'key': 'moduleEnabled', 'value': 'True'}],
            'resourcePrefix': 'customer-prefix_AZ390 ',
        },
        groups=[group.name],
    )
    assert 'InvalidInput' in response.errors[0].message

    response = client.query(
        query,
        username='alice',
        environmentUri=env_fixture.environmentUri,
        input={
            'label': 'DEV',
            'tags': ['test', 'env'],
            'parameters': [{'key': 'moduleEnabled', 'value': 'True'}],
            'resourcePrefix': 'customer-prefix',
        },
        groups=[group.name],
    )
    print(response)
    assert response.data.updateEnvironment.organization.organizationUri == org_fixture.organizationUri
    assert response.data.updateEnvironment.owner == 'alice'
    assert response.data.updateEnvironment.AwsAccountId == env_fixture.AwsAccountId
    assert response.data.updateEnvironment.label == 'DEV'
    assert str(response.data.updateEnvironment.tags) == str(['test', 'env'])
    assert not response.data.updateEnvironment.dashboardsEnabled
    assert response.data.updateEnvironment.parameters
    assert response.data.updateEnvironment.parameters[0]['key'] == 'moduleEnabled'
    assert response.data.updateEnvironment.parameters[0]['value'] == 'True'
    assert response.data.updateEnvironment.resourcePrefix == 'customer-prefix'


def test_update_params(client, org_fixture, env_fixture, group):
    def update_params(parameters):
        return client.query(
            query,
            username='alice',
            environmentUri=env_fixture.environmentUri,
            input=parameters,
            groups=[group.name],
        )

    query = """
        mutation UpdateEnv($environmentUri:String!,$input:ModifyEnvironmentInput!){
            updateEnvironment(environmentUri:$environmentUri,input:$input){
                parameters {
                    key
                    value
                }
            }
        }
    """

    module_enabled = {'parameters': [{'key': 'moduleEnabled', 'value': 'True'}]}
    environment = update_params(module_enabled).data.updateEnvironment
    assert len(environment.parameters)
    assert environment.parameters[0]['key'] == 'moduleEnabled'
    assert environment.parameters[0]['value'] == 'True'


def test_unauthorized_update(client, org_fixture, env_fixture):
    response = client.query(
        """
        mutation UpdateEnv($environmentUri:String!,$input:ModifyEnvironmentInput!){
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
        environmentUri=env_fixture.environmentUri,
        input={'label': 'DEV', 'tags': ['test', 'env']},
    )
    assert 'UnauthorizedOperation' in response.errors[0].message


def test_list_environments_no_filter(org_fixture, env_fixture, client, group):
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


def test_list_environment_role_filter_as_creator(org_fixture, env_fixture, client, group):
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


def test_list_environment_role_filter_as_admin(db, client, org_fixture, env_fixture, user, group):
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
        username=user.username,
        groups=[group.name],
        filter={'roles': [EnvironmentPermission.Invited.name]},
    )

    assert response.data.listEnvironments.count == 1


def test_paging(db, client, org_fixture, env_fixture, user, group):
    for i in range(1, 30):
        with db.scoped_session() as session:
            env = Environment(
                organizationUri=org_fixture.organizationUri,
                AwsAccountId=f'12345678901+{i}',
                region='eu-west-1',
                label='org',
                owner=user.username,
                tags=[],
                description='desc',
                SamlGroupName=group.name,
                EnvironmentDefaultIAMRoleName='EnvRole',
                EnvironmentDefaultIAMRoleArn='arn:aws::123456789012:role/EnvRole',
                CDKRoleArn='arn:aws::123456789012:role/EnvRole',
                userRoleInEnvironment=EnvironmentPermission.Owner.value,
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
            username=user.username,
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


def test_group_invitation(db, client, env_fixture, org_fixture, group2, user, group3, group, mocker):
    response = client.query(
        """
        query listEnvironmentGroupInvitationPermissions{
            listEnvironmentGroupInvitationPermissions{
                    permissionUri
                    name
                    type
            }
        }
        """,
        username=user.username,
        groups=[group.name, group2.name],
        filter={},
    )

    env_permissions = [p.name for p in response.data.listEnvironmentGroupInvitationPermissions]
    mocker.patch(
        'dataall.core.environment.services.managed_iam_policies.PolicyManager.create_all_policies', return_value=True
    )
    mocker.patch(
        'dataall.core.organizations.db.organization_repositories.OrganizationRepository.find_group_membership',
        return_value=True,
    )

    response = client.query(
        """
        mutation inviteGroupOnEnvironment($input:InviteGroupOnEnvironmentInput!){
            inviteGroupOnEnvironment(input:$input){
                environmentUri
            }
        }
        """,
        username='alice',
        input=dict(
            environmentUri=env_fixture.environmentUri,
            groupUri=group2.name,
            permissions=env_permissions,
            environmentIAMRoleArn=f'arn:aws::{env_fixture.AwsAccountId}:role/myteamrole',
        ),
        groups=[group.name, group2.name],
    )
    print(response)
    assert response.data.inviteGroupOnEnvironment

    response = client.query(
        """
        query getGroup($groupUri:String!, $environmentUri:String!){
            getGroup(groupUri:$groupUri){
                environmentPermissions(environmentUri:$environmentUri){
                 name
                }
            }
        }
        """,
        username=user.username,
        groups=[group2.name],
        groupUri=group2.name,
        environmentUri=env_fixture.environmentUri,
    )
    env_permissions = [p.name for p in response.data.getGroup.environmentPermissions]

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
            environmentUri=env_fixture.environmentUri,
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
        username=user.username,
        groups=[group.name, group2.name],
        environmentUri=env_fixture.environmentUri,
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
        username=user.username,
        groups=[group.name, group2.name],
        environmentUri=env_fixture.environmentUri,
        filter={},
    )

    assert response.data.listEnvironmentGroups.count == 2
    assert 'myteamrole' in [g.environmentIAMRoleName for g in response.data.listEnvironmentGroups.nodes]

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
        username=user.username,
        groups=[group.name],
        environmentUri=env_fixture.environmentUri,
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
        username=user.username,
        groups=[group.name],
        environmentUri=env_fixture.environmentUri,
        filter={},
    )

    assert response.data.listAllEnvironmentGroups.count == 2

    mocker.patch(
        'dataall.core.environment.services.managed_iam_policies.PolicyManager.delete_all_policies', return_value=True
    )
    response = client.query(
        """
        mutation removeGroupFromEnvironment($environmentUri: String!, $groupUri: String!){
            removeGroupFromEnvironment(environmentUri: $environmentUri, groupUri: $groupUri){
                environmentUri
            }
        }
        """,
        username='alice',
        environmentUri=env_fixture.environmentUri,
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
        username=user.username,
        groups=[group.name, group2.name],
        environmentUri=env_fixture.environmentUri,
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
        username=user.username,
        groups=[group.name, group2.name],
        environmentUri=env_fixture.environmentUri,
        filter={},
    )

    assert response.data.listEnvironmentGroups.count == 1

    response = client.query(
        """
        mutation inviteGroupOnEnvironment($input:InviteGroupOnEnvironmentInput!){
            inviteGroupOnEnvironment(input:$input){
                environmentUri
            }
        }
        """,
        username='alice',
        input=dict(
            environmentUri=env_fixture.environmentUri,
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
        username=user.username,
        groups=[group.name, group2.name, group3.name],
        environmentUri=env_fixture.environmentUri,
        filter={},
    )
    assert 'myteamrole' not in [g.environmentIAMRoleName for g in response.data.listEnvironmentGroups.nodes]


def test_archive_env(client, org_fixture, env, group, group2, mocker):
    env_fixture = env(org_fixture, 'dev-delete', 'alice', 'testadmins', '111111111111', 'eu-west-2')
    mocker.patch(
        'dataall.core.environment.services.managed_iam_policies.PolicyManager.delete_all_policies', return_value=True
    )
    response = client.query(
        """
        mutation deleteEnvironment($environmentUri:String!, $deleteFromAWS:Boolean!){
            deleteEnvironment(environmentUri:$environmentUri, deleteFromAWS:$deleteFromAWS)
        }
        """,
        username='alice',
        groups=[group.name, group2.name],
        environmentUri=env_fixture.environmentUri,
        deleteFromAWS=True,
    )
    print(response)
    assert response.data.deleteEnvironment


def test_create_environment(db, client, org_fixture, user, group):
    response = client.query(
        """mutation CreateEnv($input:NewEnvironmentInput!){
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
        username=user.username,
        groups=[group.name],
        input={
            'label': f'dev',
            'description': f'test',
            'EnvironmentDefaultIAMRoleArn': 'arn:aws:iam::444444444444:role/myOwnIamRole',
            'organizationUri': org_fixture.organizationUri,
            'AwsAccountId': '444444444444',
            'tags': ['a', 'b', 'c'],
            'region': 'eu-west-1',
            'SamlGroupName': group.name,
            'resourcePrefix': 'customer-prefix',
        },
    )

    body = response.data.createEnvironment

    assert len(body.networks) == 0
    assert body.EnvironmentDefaultIAMRoleName == 'myOwnIamRole'
    assert body.EnvironmentDefaultIAMRoleImported
    assert body.resourcePrefix == 'customer-prefix'

    with db.scoped_session() as session:
        env = EnvironmentService.get_environment_by_uri(session, response.data.createEnvironment.environmentUri)
        session.delete(env)
        session.commit()


def test_update_consumption_role(client, org_fixture, env_fixture, user, group, db, consumption_role):
    query = """
        mutation updateConsumptionRole(
            $environmentUri:String!,
            $consumptionRoleUri:String!,
            $input:UpdateConsumptionRoleInput
        ){
            updateConsumptionRole(
                environmentUri:$environmentUri,
                consumptionRoleUri: $consumptionRoleUri,
                input:$input
            ){
                consumptionRoleUri
                consumptionRoleName
                environmentUri
                groupUri
                IAMRoleName
                IAMRoleArn
            }
        }
    """

    consumption_role_uri = consumption_role.data.addConsumptionRoleToEnvironment.consumptionRoleUri

    with db.scoped_session() as session:
        ResourcePolicyService.attach_resource_policy(
            session=session,
            resource_uri=consumption_role_uri,
            group=group.name,
            permissions=[REMOVE_ENVIRONMENT_CONSUMPTION_ROLE],
            resource_type=Environment.__name__,
        )

    response = client.query(
        query,
        username=user,
        groups=[group.name],
        environmentUri=env_fixture.environmentUri,
        consumptionRoleUri=consumption_role_uri,
        input={'consumptionRoleName': 'testRoleName', 'groupUri': 'testGroupUri'},
    )

    assert not response.errors
    assert response.data.updateConsumptionRole.consumptionRoleName == 'testRoleName'
    assert response.data.updateConsumptionRole.groupUri == 'testGroupUri'
