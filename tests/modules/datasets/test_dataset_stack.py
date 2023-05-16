from tests.api.test_stack import update_stack_query


def test_notebook_stack(client, dataset_fixture, group):
    dataset = dataset_fixture
    response = update_stack_query(client, dataset.datasetUri, 'dataset', dataset.SamlAdminGroupName)
    assert response.data.updateStack.targetUri == dataset.datasetUri
