import pytest


class MockSagemakerClient:
    def start_instance(self):
        return "Starting"

    def stop_instance(self):
        return True

    def get_notebook_instance_status(self):
        return "INSERVICE"



@pytest.fixture(scope='module')
def org1(org, user, group, tenant):
    org1 = org('testorg', user.userName, group.name)
    yield org1


@pytest.fixture(scope='module')
def env1(env, org1, user, group, tenant, db, module_mocker):
    module_mocker.patch('requests.post', return_value=True)
    module_mocker.patch(
        'dataall.api.Objects.Environment.resolvers.check_environment', return_value=True
    )
    env1 = env(org1, 'dev', user.userName, group.name, '111111111111', 'eu-west-1',
               parameters={"notebooksEnabled": "True"})
    yield env1


def test_sgm_notebook(sgm_notebook, group):
    assert sgm_notebook.notebookUri
    assert sgm_notebook.SamlAdminGroupName == group.name
    assert sgm_notebook.VpcId == 'vpc-123567'
    assert sgm_notebook.SubnetId == 'subnet-123567'
    assert sgm_notebook.InstanceType == 'ml.m5.xlarge'
    assert sgm_notebook.VolumeSizeInGB == 32


@pytest.fixture(scope='module', autouse=True)
def patch_aws(module_mocker):
    module_mocker.patch(
        "dataall.modules.notebooks.services.services.client",
        return_value=MockSagemakerClient(),
    )


def test_list_notebooks(client, user, group, sgm_notebook):
    query = """
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
        """

    response = client.query(
        query,
        filter=None,
        username=user.userName,
        groups=[group.name],
    )

    assert len(response.data.listSagemakerNotebooks['nodes']) == 1

    response = client.query(
        query,
        filter={"term": "my best"},
        username=user.userName,
        groups=[group.name],
    )

    assert len(response.data.listSagemakerNotebooks['nodes']) == 1


def test_nopermissions_list_notebooks(client, user2, group2, sgm_notebook):
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


def test_get_notebook(client, user, group, sgm_notebook):

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


def test_action_notebook(client, user, group, sgm_notebook):
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


def test_delete_notebook(client, user, group, sgm_notebook):

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
