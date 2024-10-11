from assertpy import assert_that
import pytest
from boto3 import client

from deploy.app import response
from integration_tests.errors import GqlError
from integration_tests.modules.redshift_datasets.dataset_queries import (
    list_redshift_dataset_tables,
    import_redshift_dataset,
)
from integration_tests.modules.redshift_datasets.global_conftest import (
    REDSHIFT_SCHEMA,
    REDSHIFT_TABLE1,
    REDSHIFT_TABLE2,
)


def test_import_redshift_serverless_dataset_with_table(client1, session_redshift_dataset_serverless):
    assert_that(session_redshift_dataset_serverless.datasetUri).is_not_none()
    assert_that(session_redshift_dataset_serverless.datasetType).is_equal_to('Redshift')
    tables = list_redshift_dataset_tables(client=client1, dataset_uri=session_redshift_dataset_serverless.datasetUri)
    assert_that(tables.count).is_equal_to(1)
    assert_that(tables.nodes[0].name).is_equal_to(REDSHIFT_TABLE1)


def test_import_redshift_cluster_dataset_without_table(client5, session_redshift_dataset_cluster):
    assert_that(session_redshift_dataset_cluster.datasetUri).is_not_none()
    assert_that(session_redshift_dataset_cluster.datasetType).is_equal_to('Redshift')
    tables = list_redshift_dataset_tables(client=client5, dataset_uri=session_redshift_dataset_cluster.datasetUri)
    assert_that(tables.count).is_equal_to(0)


def test_import_redshift_unauthorized(client2, user1, group1, session_env1, session_redshift_dataset_serverless):
    assert_that(import_redshift_dataset).raises(GqlError).when_called_with(
        client=client2,
        label='Error-Test-Redshift-Serverless',
        org_uri=session_env1.organizationUri,
        env_uri=session_env1.environmentUri,
        description='Error',
        tags=[],
        owner=user1.username,
        group_uri=group1,
        confidentiality='Secret',
        auto_approval_enabled=False,
        connection_uri=session_redshift_dataset_serverless.connectionUri,
        schema=REDSHIFT_SCHEMA,
        tables=[],
    ).contains('UnauthorizedOperation', 'IMPORT_REDSHIFT_DATASET', session_env1.environmentUri)


def test_update_redshift_dataset(client1):
    pass


def test_delete_redshift_dataset(client1):
    pass


def test_add_redshift_dataset_tables(client1):
    pass


def test_delete_redshift_dataset_table(client1):
    pass


def test_update_redshift_dataset_table(client1):
    pass


def test_get_redshift_dataset(client1):
    pass


def test_list_redshift_dataset_tables(client1):
    pass


def test_get_redshift_dataset_table(client1):
    pass


def test_get_redshift_dataset_table_columns(client1):
    pass


def test_list_redshift_schema_dataset_tables(client1):
    pass
