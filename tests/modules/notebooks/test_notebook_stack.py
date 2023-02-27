
def test_notebook_stack(client, sgm_notebook, group):
    response = client.query(
        """
        mutation updateStack($targetUri:String!, $targetType:String!){
            updateStack(targetUri:$targetUri, targetType:$targetType){
                stackUri
                targetUri
                name
            }
        }
        """,
        targetUri=sgm_notebook.notebookUri,
        targetType="notebook",
        username="alice",
        groups=[group.name],
    )
    assert response.data.updateStack.targetUri == sgm_notebook.notebookUri