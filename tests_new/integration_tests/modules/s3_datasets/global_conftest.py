import logging

import pytest

from integration_tests.client import GqlError
from integration_tests.core.stack.utils import check_stack_ready

from integration_tests.modules.s3_datasets.queries import (
    create_dataset,
    import_dataset,
    delete_dataset,
    get_dataset,
)
from tests_new.integration_tests.modules.datasets_base.queries import list_datasets

log = logging.getLogger(__name__)


def create_s3_dataset(
    client, owner, group, org_uri, env_uri, dataset_name, tags=[], autoApprovalEnabled=False, confidentiality=None
):
    dataset = create_dataset(
        client,
        name=dataset_name,
        owner=owner,
        group=group,
        organizationUri=org_uri,
        environmentUri=env_uri,
        tags=tags,
        autoApprovalEnabled=autoApprovalEnabled,
        confidentiality=confidentiality,
    )
    check_stack_ready(client, env_uri, dataset.stack.stackUri)
    return get_dataset(client, dataset.datasetUri)


def import_s3_dataset(
    client,
    owner,
    group,
    org_uri,
    env_uri,
    dataset_name,
    bucket,
    kms_alias='',
    glue_db_name='',
    tags=[],
    autoApprovalEnabled=False,
    confidentiality=None,
):
    dataset = import_dataset(
        client,
        name=dataset_name,
        owner=owner,
        group=group,
        organizationUri=org_uri,
        environmentUri=env_uri,
        tags=tags,
        bucketName=bucket,
        KmsKeyAlias=kms_alias,
        glueDatabaseName=glue_db_name,
        autoApprovalEnabled=autoApprovalEnabled,
        confidentiality=confidentiality,
    )
    check_stack_ready(client, env_uri, dataset.stack.stackUri)
    return get_dataset(client, dataset.datasetUri)


def delete_s3_dataset(client, env_uri, dataset):
    check_stack_ready(client, env_uri, dataset.stack.stackUri)
    try:
        return delete_dataset(client, dataset.datasetUri)
    except GqlError:
        log.exception('unexpected error when deleting dataset')
        return False


"""
Session envs persist accross the duration of the whole integ test suite and are meant to make the test suite run faster (env creation takes ~2 mins).
For this reason they must stay immutable as changes to them will affect the rest of the tests.
"""


@pytest.fixture(scope='session')
def session_s3_dataset1(client1, group1, org1, session_env1, session_id, testdata):
    envdata = testdata.datasets['session_s3_dataset1']
    ds = None
    try:
        ds = create_s3_dataset(
            client1,
            owner='someone',
            group=group1,
            org_uri=org1['organizationUri'],
            env_uri=session_env1['environmentUri'],
            dataset_name=envdata.name,
            tags=[session_id],
        )
        yield ds
    finally:
        if ds:
            delete_s3_dataset(client1, session_env1['environmentUri'], ds)


@pytest.fixture(scope='session')
def session_imported_sse_s3_dataset1(client1, group1, org1, session_env1, session_id, testdata):
    envdata = testdata.datasets['session_imported_sse_s3_dataset1']
    ds = None
    try:
        # TODO: Create S3 Bucket before import + Clean Up in Finally
        ds = import_s3_dataset(
            client1,
            owner='someone',
            group=group1,
            org_uri=org1['organizationUri'],
            env_uri=session_env1['environmentUri'],
            dataset_name=envdata.name,
            tags=[session_id],
            bucket=envdata.bucket,
        )
        yield ds
    finally:
        if ds:
            delete_s3_dataset(client1, session_env1['environmentUri'], ds)


@pytest.fixture(scope='session')
def session_imported_kms_s3_dataset1(client1, group1, org1, session_env1, session_id, testdata):
    envdata = testdata.datasets['session_imported_kms_s3_dataset1']
    ds = None
    try:
        # TODO: Create S3 Bucket, KMS, + Glue DB before import + Clean Up in Finally
        ds = import_s3_dataset(
            client1,
            owner='someone',
            group=group1,
            org_uri=org1['organizationUri'],
            env_uri=session_env1['environmentUri'],
            dataset_name=envdata.name,
            tags=[session_id],
            bucket=envdata.bucket,
            kms_alias=envdata.kmsAlias,
            glue_db_name=envdata.glueDatabaseName,
        )
        yield ds
    finally:
        if ds:
            delete_s3_dataset(client1, session_env1['environmentUri'], ds)


"""
Temp envs will be created and deleted per test, use with caution as they might increase the runtime of the test suite.
They are suitable to test env mutations.
"""


@pytest.fixture(scope='function')
def temp_s3_dataset1(client1, group1, org1, session_env1, session_id, testdata):
    envdata = testdata.datasets['temp_s3_dataset1']
    ds = None
    try:
        ds = create_s3_dataset(
            client1,
            owner='someone',
            group=group1,
            org_uri=org1['organizationUri'],
            env_uri=session_env1['environmentUri'],
            dataset_name=envdata.name,
            tags=[session_id],
        )
        yield ds
    finally:
        if ds:
            delete_s3_dataset(client1, session_env1['environmentUri'], ds)


"""
Persistent environments must always be present (if not i.e first run they will be created but won't be removed).
They are suitable for testing backwards compatibility. 
"""


def get_or_create_persistent_s3_dataset(dataset_name, client, group, env, testdata):
    s3_datasets = list_datasets(client, term=dataset_name).nodes
    if s3_datasets:
        return s3_datasets[0]
    else:
        s3_dataset_data = testdata.datasets[dataset_name]

        if s3_dataset_data.bucket:
            s3_dataset = import_s3_dataset(
                client,
                owner='someone',
                group=group,
                org_uri=env['organization']['organizationUri'],
                env_uri=env['environmentUri'],
                dataset_name=dataset_name,
                tags=[dataset_name],
                bucket=s3_dataset_data.bucket,
                kms_alias=s3_dataset_data.kmsAlias,
                glue_db_name=s3_dataset_data.glueDatabaseName,
            )

        else:
            s3_dataset = create_s3_dataset(
                client,
                owner='someone',
                group=group,
                org_uri=env['organization']['organizationUri'],
                env_uri=env['environmentUri'],
                dataset_name=dataset_name,
                tags=[dataset_name],
            )

        if s3_dataset.stack.status in ['CREATE_COMPLETE', 'UPDATE_COMPLETE']:
            return s3_dataset
        else:
            delete_s3_dataset(client, env['environmentUri'], s3_dataset.datasetUri)
            raise RuntimeError(f'failed to create {dataset_name=} {s3_dataset=}')


@pytest.fixture(scope='session')
def persistent_s3_dataset1(client1, group1, persistent_env1, testdata):
    return get_or_create_persistent_s3_dataset('persistent_s3_dataset1', client1, group1, persistent_env1, testdata)


@pytest.fixture(scope='session')
def persistent_imported_sse_s3_dataset1(client1, group1, persistent_env1, testdata):
    return get_or_create_persistent_s3_dataset(
        'persistent_imported_sse_s3_dataset1', client1, group1, persistent_env1, testdata
    )


@pytest.fixture(scope='session')
def persistent_imported_kms_s3_dataset1(client1, group1, persistent_env1, testdata):
    return get_or_create_persistent_s3_dataset(
        'persistent_imported_kms_s3_dataset1', client1, group1, persistent_env1, testdata
    )
