def test_sagemaker_studio_update_stack(client, sagemaker_studio_user, group):
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
        targetUri=sagemaker_studio_user.sagemakerStudioUserUri,
        targetType='mlstudio',
        username='alice',
        groups=[group.name],
    )
    assert response.data.updateStack.targetUri == sagemaker_studio_user.sagemakerStudioUserUri
