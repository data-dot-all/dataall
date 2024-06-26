from dataall.modules.s3_datasets.db.dataset_models import S3Dataset
from dataall.modules.s3_datasets.services.dataset_permissions import CREATE_DATASET


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


def test_dataset_resource_found(db, client, env_fixture, org_fixture, group2, user, group3, group, dataset, mocker):
    mocker.patch(
        'dataall.core.environment.services.managed_iam_policies.PolicyManager.create_all_policies', return_value=True
    )
    mocker.patch(
        'dataall.core.environment.services.managed_iam_policies.PolicyManager.delete_all_policies', return_value=True
    )
    mocker.patch(
        'dataall.core.environment.services.managed_iam_policies.PolicyManager.delete_all_policies', return_value=True
    )
    mocker.patch(
        'dataall.core.organizations.db.organization_repositories.OrganizationRepository.find_group_membership',
        return_value=True,
    )
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
    assert CREATE_DATASET in env_permissions

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
    assert CREATE_DATASET in env_permissions

    dataset = dataset(org=org_fixture, env=env_fixture, name='dataset1', owner='bob', group=group2.name)
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
        environmentUri=env_fixture.environmentUri,
        groupUri=group2.name,
        groups=[group.name, group2.name],
    )
    print(response)

    assert 'EnvironmentResourcesFound' in response.errors[0].message
    with db.scoped_session() as session:
        dataset = session.query(S3Dataset).get(dataset.datasetUri)
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
        environmentUri=env_fixture.environmentUri,
        groupUri=group2.name,
        groups=[group.name, group2.name],
    )
    print(response)
    assert response.data.removeGroupFromEnvironment
