def test_update_stack(
    client,
    tenant,
    group,
    env_fixture,
):
    response = update_stack_query(client, env_fixture.environmentUri, 'environment', group.name)
    assert response.data.updateStack.targetUri == env_fixture.environmentUri


def update_stack_query(client, target_uri, target_type, group):
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
        targetUri=target_uri,
        targetType=target_type,
        username='alice',
        groups=[group],
    )
    return response
