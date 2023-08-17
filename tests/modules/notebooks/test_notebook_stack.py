from tests.core.stacks.test_stack import update_stack_query


def test_notebook_stack(client, sgm_notebook, group):
    response = update_stack_query(client, sgm_notebook.notebookUri, 'notebook', group.name)
    assert response.data.updateStack.targetUri == sgm_notebook.notebookUri
