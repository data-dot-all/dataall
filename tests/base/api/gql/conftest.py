import pytest

from dataall.base.api import gql


@pytest.fixture(scope='function', autouse=True)
def reset():
    tmp = (gql.ObjectType.class_instances, gql.QueryField.class_instances, gql.MutationField.class_instances)
    gql.ObjectType.class_instances = {}
    gql.QueryField.class_instances = {}
    gql.MutationField.class_instances = {}

    yield

    gql.ObjectType.class_instances, gql.QueryField.class_instances, gql.MutationField.class_instances = tmp
