from typing import List

import dataall
from dataall.db import models
import pytest

from dataall.db import exceptions


@pytest.fixture(scope='module')
def org1(db, org, tenant, user, group) -> models.Organization:
    org = org('testorg', user.userName, group.name)
    yield org


@pytest.fixture(scope='module')
def env1(
    db, org1: models.Organization, user, group, module_mocker, env
) -> models.Environment:
    module_mocker.patch('requests.post', return_value=True)
    module_mocker.patch(
        'dataall.api.Objects.Environment.resolvers.check_environment', return_value=True
    )
    env1 = env(org1, 'dev', user.userName, group.name, '111111111111', 'eu-west-1')
    yield env1


@pytest.fixture(scope='module', autouse=True)
def dataset1(db, env1, org1, group, user, dataset) -> models.Dataset:
    with db.scoped_session() as session:
        yield dataset(
            org=org1, env=env1, name='dataset1', owner=user.userName, group=group.name
        )


def list_tags_query(client, dataset1, target_type=None):
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
        targetUri=dataset1.datasetUri,
        targetType=target_type or 'dataset',
        username='alice',
        groups=[dataset1.SamlAdminGroupName],
    )
    return query


def test_empty_key_value_tags(client, dataset1):
    response = list_tags_query(client, dataset1)
    print(response)
    assert len(response.data.listKeyValueTags) == 0


def test_unsupported_target_type(db, dataset1):
    with pytest.raises(exceptions.InvalidInput):
        assert dataall.db.api.TargetType.is_supported_target_type('unknown')


def test_update_key_value_tags(client, dataset1):
    response = client.query(
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
        input=dict(
            targetUri=dataset1.datasetUri,
            targetType='dataset',
            tags=[{'key': 'tag1', 'value': 'value1', 'cascade': False}],
        ),
        username='alice',
        groups=[dataset1.SamlAdminGroupName],
    )
    assert len(response.data.updateKeyValueTags) == 1

    response = list_tags_query(client, dataset1)
    assert response.data.listKeyValueTags[0].key == 'tag1'
    assert response.data.listKeyValueTags[0].value == 'value1'
    assert response.data.listKeyValueTags[0].cascade == False

    response = client.query(
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
        input=dict(targetUri=dataset1.datasetUri, targetType='dataset', tags=[]),
        username='alice',
        groups=[dataset1.SamlAdminGroupName],
    )
    assert len(response.data.updateKeyValueTags) == 0

    response = list_tags_query(client, dataset1)
    assert len(response.data.listKeyValueTags) == 0
