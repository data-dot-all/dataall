import typing
import pytest

import dataall

class MockSagemakerStudioClient:
    def get_sagemaker_studio_user_presigned_url(self):
        return "someurl"

    def get_sagemaker_studio_user_status(self):
        return "InService"

    def get_sagemaker_studio_user_applications(self):
        return []


def test_create_sagemaker_studio_user(sagemaker_studio_user, group, env_fixture):
    """Testing that the conftest sagemaker studio user has been created correctly"""
    assert sagemaker_studio_user.label == 'testcreate'
    assert sagemaker_studio_user.SamlAdminGroupName ==group.name
    assert sagemaker_studio_user.environmentUri == env_fixture.environmentUri


def test_list_sagemaker_studio_users(client, env_fixture, db, group, multiple_sagemaker_studio_users):
    response = client.query(
        """
        query listSagemakerStudioUsers($filter:SagemakerStudioUserFilter!){
            listSagemakerStudioUsers(filter:$filter){
                count
                nodes{
                    sagemakerStudioUserUri
                }
            }
        }
        """,
        filter={},
        username='alice',
    )
    print(response.data)
    assert len(response.data.listSagemakerStudioUsers['nodes']) == 140


def test_nopermissions_list_sagemaker_studio_users(
    client, db, group
):
    response = client.query(
        """
        query listSagemakerStudioUsers($filter:SagemakerStudioUserFilter!){
            listSagemakerStudioUsers(filter:$filter){
                count
                nodes{
                    sagemakerStudioUserUri
                }
            }
        }
        """,
        filter={},
        username='bob',
    )
    assert len(response.data.listSagemakerStudioUsers['nodes']) == 0


def test_delete_sagemaker_studio_user(
    client, db, module_mocker, group
):
    with db.scoped_session() as session:
        sm_user = session.query(
            dataall.modules.mlstudio.db.models.SagemakerStudioUser
        ).first()
    module_mocker.patch(
        'dataall.aws.handlers.service_handlers.Worker.queue', return_value=True
    )
    response = client.query(
        """
        mutation deleteSagemakerStudioUser($sagemakerStudioUserUri:String!, $deleteFromAWS:Boolean){
            deleteSagemakerStudioUser(sagemakerStudioUserUri:$sagemakerStudioUserUri, deleteFromAWS:$deleteFromAWS)
        }
        """,
        sagemakerStudioUserUri=sm_user.sagemakerStudioUserUri,
        deleteFromAWS=True,
        username='alice',
        groups=[group.name],
    )
    assert response.data
    with db.scoped_session() as session:
        n = session.query(dataall.modules.mlstudio.db.models.SagemakerStudioUser).get(
            sm_user.sagemakerStudioUserUri
        )
        assert not n
