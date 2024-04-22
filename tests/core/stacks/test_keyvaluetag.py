import pytest

from dataall.core.stacks.db.target_type_repositories import TargetType
from dataall.base.db import exceptions


def list_tags_query(client, target_uri, target_type, group):
    query = client.query(
        """
        query listKeyValueTags($targetUri:String!, $targetType:String!){
            listKeyValueTags(targetUri:$targetUri, targetType:$targetType){
                tagUri
                targetUri
                targetType
                key
                value
                cascade
            }
        }
        """,
        targetUri=target_uri,
        targetType=target_type,
        username='alice',
        groups=[group],
    )
    return query


def test_unsupported_target_type(db):
    with pytest.raises(exceptions.InvalidInput):
        assert TargetType.is_supported_target_type('unknown')


def update_key_value_tags(client, target_uri, target_type, tags, group):
    return client.query(
        """
            mutation updateKeyValueTags($input:UpdateKeyValueTagsInput!){
                updateKeyValueTags(input:$input){
                    tagUri
                    targetUri
                    targetType
                    key
                    value
                    cascade
                }
            }
            """,
        input=dict(targetUri=target_uri, targetType=target_type, tags=tags),
        username='alice',
        groups=[group],
    )
