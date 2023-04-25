import pytest

import dataall


@pytest.fixture(scope='module')
def org1(org, user, group, tenant):
    org1 = org('testorg', user.userName, group.name)
    yield org1


@pytest.fixture(scope='module')
def env1(env, org1, user, group, tenant, module_mocker):
    env1 = env(org1, 'dev', user.userName, group.name, '111111111111', 'eu-west-1')
    yield env1


@pytest.fixture(scope='module', autouse=True)
def sgm_notebook(client, tenant, group, env1) -> dataall.db.models.SagemakerNotebook:
    response = client.query(
        """
        mutation createSagemakerNotebook($input:NewSagemakerNotebookInput){
            createSagemakerNotebook(input:$input){
                notebookUri
                label
                description
                tags
                owner
                userRoleForNotebook
                SamlAdminGroupName
                VpcId
                SubnetId
                VolumeSizeInGB
                InstanceType
            }
        }
        """,
        input={
            'label': 'my pipeline',
            'SamlAdminGroupName': group.name,
            'tags': [group.name],
            'environmentUri': env1.environmentUri,
            'VpcId': 'vpc-123567',
            'SubnetId': 'subnet-123567',
            'VolumeSizeInGB': 32,
            'InstanceType': 'ml.m5.xlarge',
        },
        username='alice',
        groups=[group.name],
    )
    assert response.data.createSagemakerNotebook.notebookUri
    assert response.data.createSagemakerNotebook.SamlAdminGroupName == group.name
    assert response.data.createSagemakerNotebook.VpcId == 'vpc-123567'
    assert response.data.createSagemakerNotebook.SubnetId == 'subnet-123567'
    assert response.data.createSagemakerNotebook.InstanceType == 'ml.m5.xlarge'
    assert response.data.createSagemakerNotebook.VolumeSizeInGB == 32
    return response.data.createSagemakerNotebook


@pytest.fixture(scope='module', autouse=True)
def patch_aws(module_mocker):
    module_mocker.patch(
        'dataall.aws.handlers.sagemaker.Sagemaker.start_instance',
        return_value='Starting',
    )
    module_mocker.patch(
        'dataall.aws.handlers.sagemaker.Sagemaker.stop_instance', return_value=True
    )
    module_mocker.patch(
        'dataall.aws.handlers.sagemaker.Sagemaker.get_notebook_instance_status',
        return_value='INSERVICE',
    )


def test_list_notebooks(client, env1, db, org1, user, group, sgm_notebook, patch_aws):
    response = client.query(
        """
        query ListSagemakerNotebooks($filter:SagemakerNotebookFilter){
            listSagemakerNotebooks(filter:$filter){
                count
                nodes{
                    NotebookInstanceStatus
                    notebookUri
                    environment {
                     environmentUri
                    }
                    organization {
                     organizationUri
                    }
                }
            }
        }
        """,
        filter=None,
        username=user.userName,
        groups=[group.name],
    )
    assert len(response.data.listSagemakerNotebooks['nodes']) == 1


def test_nopermissions_list_notebooks(
    client, env1, db, org1, user2, group2, sgm_notebook, patch_aws
):
    response = client.query(
        """
        query ListSagemakerNotebooks($filter:SagemakerNotebookFilter){
            listSagemakerNotebooks(filter:$filter){
                count
                nodes{
                    NotebookInstanceStatus
                    notebookUri
                    environment {
                     environmentUri
                    }
                    organization {
                     organizationUri
                    }
                }
            }
        }
        """,
        filter=None,
        username=user2.userName,
        groups=[group2.name],
    )
    assert len(response.data.listSagemakerNotebooks['nodes']) == 0


def test_get_notebook(client, env1, db, org1, user, group, sgm_notebook, patch_aws):

    response = client.query(
        """
        query getSagemakerNotebook($notebookUri:String!){
            getSagemakerNotebook(notebookUri:$notebookUri){
                notebookUri
                NotebookInstanceStatus
            }
        }
        """,
        notebookUri=sgm_notebook.notebookUri,
        username=user.userName,
        groups=[group.name],
    )
    assert response.data.getSagemakerNotebook.notebookUri == sgm_notebook.notebookUri


def test_action_notebook(client, env1, db, org1, user, group, sgm_notebook, patch_aws):
    response = client.query(
        """
        mutation stopSagemakerNotebook($notebookUri:String!){
            stopSagemakerNotebook(notebookUri:$notebookUri)
        }
        """,
        notebookUri=sgm_notebook.notebookUri,
        username=user.userName,
        groups=[group.name],
    )
    assert response.data.stopSagemakerNotebook == 'Stopping'

    response = client.query(
        """
        mutation startSagemakerNotebook($notebookUri:String!){
            startSagemakerNotebook(notebookUri:$notebookUri)
        }
        """,
        notebookUri=sgm_notebook.notebookUri,
        username=user.userName,
        groups=[group.name],
    )
    assert response.data.startSagemakerNotebook == 'Starting'


def test_delete_notebook(client, env1, db, org1, user, group, patch_aws, sgm_notebook):

    response = client.query(
        """
        mutation deleteSagemakerNotebook($notebookUri:String!,$deleteFromAWS:Boolean){
            deleteSagemakerNotebook(notebookUri:$notebookUri,deleteFromAWS:$deleteFromAWS)
        }
        """,
        notebookUri=sgm_notebook.notebookUri,
        deleteFromAWS=True,
        username=user.userName,
        groups=[group.name],
    )
    assert response.data.deleteSagemakerNotebook
    response = client.query(
        """
        query ListSagemakerNotebooks($filter:SagemakerNotebookFilter){
            listSagemakerNotebooks(filter:$filter){
                count
                nodes{
                    NotebookInstanceStatus
                    notebookUri
                    environment {
                     environmentUri
                    }
                    organization {
                     organizationUri
                    }
                }
            }
        }
        """,
        filter=None,
        username=user.userName,
        groups=[group.name],
    )
    assert len(response.data.listSagemakerNotebooks['nodes']) == 0
