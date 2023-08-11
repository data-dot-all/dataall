from dataall.core.organizations.db.organization_models import Organization
import pytest

from dataall.core.environment.db.models import Environment
from dataall.modules.datasets_base.db.models import Dataset
from tests.core.stacks.test_keyvaluetag import update_key_value_tags, list_tags_query


@pytest.fixture(scope='module')
def org1(db, org, tenant, user, group) -> Organization:
    org = org('testorg', user.username, group.name)
    yield org


@pytest.fixture(scope='module')
def env1(
        db, org1: Organization, user, group, module_mocker, env
) -> Environment:
    module_mocker.patch('requests.post', return_value=True)
    module_mocker.patch(
        'dataall.core.environment.api.resolvers.check_environment', return_value=True
    )
    env1 = env(org1, 'dev', user.username, group.name, '111111111111', 'eu-west-1')
    yield env1


@pytest.fixture(scope='module', autouse=True)
def dataset1(db, env1, org1, group, user, dataset) -> Dataset:
    with db.scoped_session():
        yield dataset(
            org=org1, env=env1, name='dataset1', owner=user.username, group=group.name
        )


def list_dataset_tags_query(client, dataset):
    return list_tags_query(client, dataset.datasetUri, 'dataset', dataset.SamlAdminGroupName)


def test_empty_key_value_tags(client, dataset1):
    response = list_dataset_tags_query(client, dataset1)
    print(response)
    assert len(response.data.listKeyValueTags) == 0


def test_update_key_value_tags(client, dataset1):
    tags = [{'key': 'tag1', 'value': 'value1', 'cascade': False}]
    response = update_key_value_tags(client, dataset1.datasetUri, 'dataset', tags, dataset1.SamlAdminGroupName)

    assert len(response.data.updateKeyValueTags) == 1

    response = list_dataset_tags_query(client, dataset1)
    assert response.data.listKeyValueTags[0].key == 'tag1'
    assert response.data.listKeyValueTags[0].value == 'value1'
    assert not response.data.listKeyValueTags[0].cascade

    response = update_key_value_tags(client, dataset1.datasetUri, 'dataset', [], dataset1.SamlAdminGroupName)
    assert len(response.data.updateKeyValueTags) == 0

    response = list_dataset_tags_query(client, dataset1)
    assert len(response.data.listKeyValueTags) == 0
