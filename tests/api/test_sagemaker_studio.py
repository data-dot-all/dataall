import typing
import pytest

import dataall


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
    module_mocker.patch(
        'dataall.api.Objects.Environment.resolvers.get_pivot_role_as_part_of_environment', return_value=False
    )
    env1 = env(org1, 'dev', 'alice', 'testadmins', '111111111111', 'eu-west-1')
    yield env1


def test_add_sm_user_profile(client, db, env1, org1, group, module_mocker):
    module_mocker.patch(
        'dataall.aws.handlers.sagemaker_studio.SagemakerStudio.get_sagemaker_studio_domain',
        return_value={'DomainId': 'test'},
    )
    for i in range(0, 10):
        response = client.query(
            """
            mutation createSagemakerStudioUserProfile($input:NewSagemakerStudioUserProfileInput){
            createSagemakerStudioUserProfile(input:$input){
                sagemakerStudioUserProfileUri
                name
                label
                created
                description
                SamlAdminGroupName
                environmentUri
                tags
            }
        }
            """,
            input={
                'label': f'test{i}',
                'SamlAdminGroupName': group.name,
                'environmentUri': env1.environmentUri,
            },
            username='alice',
            groups=[group.name],
        )
        assert response.data.createSagemakerStudioUserProfile.label == f'test{i}'
        assert (
            response.data.createSagemakerStudioUserProfile.SamlAdminGroupName
            == group.name
        )
        assert (
            response.data.createSagemakerStudioUserProfile.environmentUri
            == env1.environmentUri
        )


def test_list_sagemaker_studio_user_profiles(client, env1, db, org1, group):
    response = client.query(
        """
        query listSagemakerStudioUserProfiles($filter:SagemakerStudioUserProfileFilter!){
            listSagemakerStudioUserProfiles(filter:$filter){
                count
                nodes{
                    sagemakerStudioUserProfileUri
                }
            }
        }
        """,
        filter={},
        username='alice',
    )
    print(response.data)
    assert len(response.data.listSagemakerStudioUserProfiles['nodes']) == 10


def test_nopermissions_list_sagemaker_studio_user_profiles(
    client, env1, db, org1, group
):
    response = client.query(
        """
        query listSagemakerStudioUserProfiles($filter:SagemakerStudioUserProfileFilter!){
            listSagemakerStudioUserProfiles(filter:$filter){
                count
                nodes{
                    sagemakerStudioUserProfileUri
                }
            }
        }
        """,
        filter={},
        username='bob',
    )
    assert len(response.data.listSagemakerStudioUserProfiles['nodes']) == 0


def test_delete_sagemaker_studio_user_profile(
    client, env1, db, org1, module_mocker, group
):
    with db.scoped_session() as session:
        sm_user_profile = session.query(
            dataall.db.models.SagemakerStudioUserProfile
        ).first()
    module_mocker.patch(
        'dataall.aws.handlers.service_handlers.Worker.queue', return_value=True
    )
    response = client.query(
        """
        mutation deleteSagemakerStudioUserProfile($sagemakerStudioUserProfileUri:String!, $deleteFromAWS:Boolean){
            deleteSagemakerStudioUserProfile(sagemakerStudioUserProfileUri:$sagemakerStudioUserProfileUri, deleteFromAWS:$deleteFromAWS)
        }
        """,
        sagemakerStudioUserProfileUri=sm_user_profile.sagemakerStudioUserProfileUri,
        deleteFromAWS=True,
        username='alice',
        groups=[group.name],
    )
    assert response.data
    with db.scoped_session() as session:
        n = session.query(dataall.db.models.SagemakerStudioUserProfile).get(
            sm_user_profile.sagemakerStudioUserProfileUri
        )
        assert not n
