import pytest

from dataall.core.environment.db.models import Environment
from dataall.core.organizations.db.organization_models import Organization
from dataall.core.stacks.db.target_type import TargetType
from dataall.base.db import exceptions


@pytest.fixture(scope='module')
def org1(db, org, tenant, user, group) -> Organization:
    org = org('testorg', user.username, group.name)
    yield org


@pytest.fixture(scope='module')
def env1(
    db, org1: Organization, user, group, module_mocker, env
) -> Environment:
    env1 = env(org1, 'dev', user.username, group.name, '111111111111', 'eu-west-1')
    yield env1


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
    return (
        client.query(
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
    )
