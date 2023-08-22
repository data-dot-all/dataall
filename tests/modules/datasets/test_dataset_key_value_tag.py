from tests.core.stacks.test_keyvaluetag import update_key_value_tags, list_tags_query


def list_dataset_tags_query(client, dataset_fixture):
    return list_tags_query(client, dataset_fixture.datasetUri, 'dataset', dataset_fixture.SamlAdminGroupName)


def test_empty_key_value_tags(client, dataset_fixture):
    response = list_dataset_tags_query(client, dataset_fixture)
    print(response)
    assert len(response.data.listKeyValueTags) == 0


def test_update_key_value_tags(client, dataset_fixture):
    tags = [{'key': 'tag1', 'value': 'value1', 'cascade': False}]
    response = update_key_value_tags(
        client, dataset_fixture.datasetUri, 'dataset', tags, dataset_fixture.SamlAdminGroupName
    )

    assert len(response.data.updateKeyValueTags) == 1

    response = list_dataset_tags_query(client, dataset_fixture)
    assert response.data.listKeyValueTags[0].key == 'tag1'
    assert response.data.listKeyValueTags[0].value == 'value1'
    assert not response.data.listKeyValueTags[0].cascade

    response = update_key_value_tags(
        client, dataset_fixture.datasetUri, 'dataset', [], dataset_fixture.SamlAdminGroupName
    )
    assert len(response.data.updateKeyValueTags) == 0

    response = list_dataset_tags_query(client, dataset_fixture)
    assert len(response.data.listKeyValueTags) == 0
