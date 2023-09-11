def test_datapipelines_update_stack_query(client, group, pipeline):
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
        targetUri=pipeline.DataPipelineUri,
        targetType='pipeline',
        username='alice',
        groups=[group.name],
    )
    assert response.data.updateStack.targetUri == pipeline.DataPipelineUri
