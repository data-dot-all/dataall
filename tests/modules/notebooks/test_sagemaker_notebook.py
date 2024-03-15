import pytest


def test_sgm_notebook(sgm_notebook, group):
    assert sgm_notebook.notebookUri
    assert sgm_notebook.SamlAdminGroupName == group.name
    assert sgm_notebook.VpcId == 'vpc-123567'
    assert sgm_notebook.SubnetId == 'subnet-123567'
    assert sgm_notebook.InstanceType == 'ml.m5.xlarge'
    assert sgm_notebook.VolumeSizeInGB == 32


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
        username=user.username,
        groups=[group.name],
    )

    assert len(response.data.listSagemakerNotebooks['nodes']) == 1

    response = client.query(
        query,
        filter={'term': 'my best'},
        username=user.username,
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
        username=user2.username,
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
        username=user.username,
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
        username=user.username,
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
        username=user.username,
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
        username=user.username,
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
        username=user.username,
        groups=[group.name],
    )
    assert len(response.data.listSagemakerNotebooks['nodes']) == 0
