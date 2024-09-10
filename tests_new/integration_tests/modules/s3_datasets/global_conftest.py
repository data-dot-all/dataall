import logging
import pytest
import boto3
import json
import os
from integration_tests.client import GqlError
from integration_tests.core.stack.utils import check_stack_ready

from integration_tests.modules.s3_datasets.queries import (
    create_dataset,
    generate_dataset_access_token,
    import_dataset,
    delete_dataset,
    get_dataset,
    sync_tables,
    create_folder,
)
from tests_new.integration_tests.modules.datasets_base.queries import list_datasets

from integration_tests.modules.s3_datasets.aws_clients import S3Client, KMSClient, GlueClient, LakeFormationClient

log = logging.getLogger(__name__)


def create_s3_dataset(client, owner, group, org_uri, env_uri, tags=[], autoApprovalEnabled=False, confidentiality=None):
    dataset = create_dataset(
        client,
        name='TestDatasetCreated',
        owner=owner,
        group=group,
        organizationUri=org_uri,
        environmentUri=env_uri,
        tags=tags,
        autoApprovalEnabled=autoApprovalEnabled,
        confidentiality=confidentiality,
    )
    check_stack_ready(
        client=client,
        env_uri=env_uri,
        stack_uri=dataset.stack.stackUri,
        target_uri=dataset.datasetUri,
        target_type='dataset',
    )
    return get_dataset(client, dataset.datasetUri)


def import_s3_dataset(
    client,
    owner,
    group,
    org_uri,
    env_uri,
    bucket,
    kms_alias='',
    glue_db_name='',
    tags=[],
    autoApprovalEnabled=False,
    confidentiality=None,
):
    dataset = import_dataset(
        client,
        name='TestDatasetImported',
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
    check_stack_ready(
        client=client,
        env_uri=env_uri,
        stack_uri=dataset.stack.stackUri,
        target_uri=dataset.datasetUri,
        target_type='dataset',
    )
    return get_dataset(client, dataset.datasetUri)


def delete_s3_dataset(client, env_uri, dataset):
    check_stack_ready(
        client=client,
        env_uri=env_uri,
        stack_uri=dataset.stack.stackUri,
        target_uri=dataset.datasetUri,
        target_type='dataset',
    )
    try:
        return delete_dataset(client, dataset.datasetUri)
    except GqlError:
        log.exception('unexpected error when deleting dataset')
        return False


def create_tables(client, dataset):
    creds = json.loads(generate_dataset_access_token(client, dataset.datasetUri))
    dataset_session = boto3.Session(
        aws_access_key_id=creds['AccessKey'],
        aws_secret_access_key=creds['SessionKey'],
        aws_session_token=creds['sessionToken'],
    )
    file_path = os.path.join(os.path.dirname(__file__), 'sample_data/csv_table/csv_sample.csv')
    S3Client(dataset_session, dataset.region).upload_file_to_prefix(
        local_file_path=file_path, s3_path=f'{dataset.S3BucketName}/integrationtest1'
    )
    GlueClient(dataset_session, dataset.region).create_table(
        database_name=dataset.GlueDatabaseName, table_name='integrationtest1', bucket=dataset.S3BucketName
    )

    S3Client(dataset_session, dataset.region).upload_file_to_prefix(
        local_file_path=file_path, s3_path=f'{dataset.S3BucketName}/integrationtest2'
    )
    GlueClient(dataset_session, dataset.region).create_table(
        database_name=dataset.GlueDatabaseName, table_name='integrationtest2', bucket=dataset.S3BucketName
    )
    response = sync_tables(client, datasetUri=dataset.datasetUri)
    return response.get('nodes', [])


def create_folders(client, dataset):
    folderA = create_folder(
        client, datasetUri=dataset.datasetUri, input={'prefix': 'sessionFolderA', 'label': 'labelSessionFolderA'}
    )
    folderB = create_folder(
        client, datasetUri=dataset.datasetUri, input={'prefix': 'sessionFolderB', 'label': 'labelSessionFolderB'}
    )

    return [folderA, folderB]


"""
Session envs persist across the duration of the whole integ test suite and are meant to make the test suite run faster (env creation takes ~2 mins).
For this reason they must stay immutable as changes to them will affect the rest of the tests.
"""


@pytest.fixture(scope='session')
def session_s3_dataset1(client1, group1, org1, session_env1, session_id, testdata):
    ds = None
    try:
        ds = create_s3_dataset(
            client1,
            owner='someone',
            group=group1,
            org_uri=org1['organizationUri'],
            env_uri=session_env1['environmentUri'],
            tags=[session_id],
            confidentiality='Unclassified',
        )
        yield ds
    finally:
        if ds:
            delete_s3_dataset(client1, session_env1['environmentUri'], ds)


@pytest.fixture(scope='session')
def session_s3_dataset1_tables(client1, session_s3_dataset1):
    yield create_tables(client1, session_s3_dataset1)


@pytest.fixture(scope='session')
def session_s3_dataset1_folders(client1, session_s3_dataset1):
    yield create_folders(client1, session_s3_dataset1)


@pytest.fixture(scope='session')
def session_imported_sse_s3_dataset1(
    client1, group1, org1, session_env1, session_id, testdata, session_env1_aws_client, resources_prefix
):
    ds = None
    bucket = None
    bucket_name = f'{resources_prefix}importedsses3'
    try:
        bucket = S3Client(session=session_env1_aws_client, region=session_env1['region']).create_bucket(
            bucket_name=bucket_name, kms_key_arn=None
        )

        ds = import_s3_dataset(
            client1,
            owner='someone',
            group=group1,
            org_uri=org1['organizationUri'],
            env_uri=session_env1['environmentUri'],
            tags=[session_id],
            bucket=bucket,
            confidentiality='Official',
        )
        if not bucket:
            raise Exception('Error creating import dataset AWS resources')
        yield ds
    finally:
        if ds:
            delete_s3_dataset(client1, session_env1['environmentUri'], ds)
        if bucket:
            S3Client(session=session_env1_aws_client, region=session_env1['region']).delete_bucket(bucket)


@pytest.fixture(scope='session')
def session_imported_sse_s3_dataset1_tables(client1, session_imported_sse_s3_dataset1):
    yield create_tables(client1, session_imported_sse_s3_dataset1)


@pytest.fixture(scope='session')
def session_imported_sse_s3_dataset1_folders(client1, session_imported_sse_s3_dataset1):
    yield create_folders(client1, session_imported_sse_s3_dataset1)


@pytest.fixture(scope='session')
def session_imported_kms_s3_dataset1(
    client1,
    group1,
    org1,
    session_env1,
    session_id,
    testdata,
    session_env1_aws_client,
    session_env1_integration_role_arn,
    resources_prefix,
):
    ds = None
    bucket = None
    database = None
    existing_lf_admins = []
    kms_alias = None
    resource_name = f'{resources_prefix}importedkms'
    try:
        kms_id, kms_alias = KMSClient(
            session=session_env1_aws_client,
            account_id=session_env1['AwsAccountId'],
            region=session_env1['region'],
        ).create_key_with_alias(resource_name)
        bucket = S3Client(session=session_env1_aws_client, region=session_env1['region']).create_bucket(
            bucket_name=resource_name,
            kms_key_arn=f"arn:aws:kms:{session_env1['region']}:{session_env1['AwsAccountId']}:key/{kms_id}",
        )
        lf_client = LakeFormationClient(session=session_env1_aws_client, region=session_env1['region'])
        existing_lf_admins = lf_client.add_role_to_datalake_admin(role_arn=session_env1_integration_role_arn)
        if lf_client.grant_create_database(role_arn=session_env1_integration_role_arn):
            database = GlueClient(session=session_env1_aws_client, region=session_env1['region']).create_database(
                database_name=resource_name, bucket=bucket
            )
        if None in [bucket, database, kms_alias]:
            raise Exception('Error creating import dataset AWS resources')
        ds = import_s3_dataset(
            client1,
            owner='someone',
            group=group1,
            org_uri=org1['organizationUri'],
            env_uri=session_env1['environmentUri'],
            tags=[session_id],
            bucket=bucket,
            kms_alias=kms_alias,
            glue_db_name=database,
            confidentiality='Secret',
        )
        yield ds
    finally:
        if ds:
            delete_s3_dataset(client1, session_env1['environmentUri'], ds)
        if bucket:
            S3Client(session=session_env1_aws_client, region=session_env1['region']).delete_bucket(bucket)
        if kms_alias:
            KMSClient(
                session=session_env1_aws_client,
                account_id=session_env1['AwsAccountId'],
                region=session_env1['region'],
            ).delete_key_by_alias(kms_alias)
        if existing_lf_admins:
            LakeFormationClient(
                session=session_env1_aws_client, region=session_env1['region']
            ).remove_role_from_datalake_admin(existing_lf_admins)
        if database:
            GlueClient(session=session_env1_aws_client, region=session_env1['region']).delete_database(database)


@pytest.fixture(scope='session')
def session_imported_kms_s3_dataset1_tables(client1, session_imported_kms_s3_dataset1):
    yield create_tables(client1, session_imported_kms_s3_dataset1)


@pytest.fixture(scope='session')
def session_imported_kms_s3_dataset1_folders(client1, session_imported_kms_s3_dataset1):
    yield create_folders(client1, session_imported_kms_s3_dataset1)


"""
Temp envs will be created and deleted per test, use with caution as they might increase the runtime of the test suite.
They are suitable to test env mutations.
"""


@pytest.fixture(scope='function')
def temp_s3_dataset1(client1, group1, org1, session_env1, session_id, testdata):
    ds = None
    try:
        ds = create_s3_dataset(
            client1,
            owner='someone',
            group=group1,
            org_uri=org1['organizationUri'],
            env_uri=session_env1['environmentUri'],
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


def get_or_create_persistent_s3_dataset(dataset_name, client, group, env, bucket=None, kms_alias='', glue_database=''):
    s3_datasets = list_datasets(client, term=dataset_name).nodes
    if s3_datasets:
        return s3_datasets[0]
    else:
        if bucket:
            s3_dataset = import_s3_dataset(
                client,
                owner='someone',
                group=group,
                org_uri=env['organization']['organizationUri'],
                env_uri=env['environmentUri'],
                tags=[dataset_name],
                bucket=bucket,
                kms_alias=kms_alias,
                glue_db_name=glue_database,
            )

        else:
            s3_dataset = create_s3_dataset(
                client,
                owner='someone',
                group=group,
                org_uri=env['organization']['organizationUri'],
                env_uri=env['environmentUri'],
                tags=[dataset_name],
            )

        if s3_dataset.stack.status in ['CREATE_COMPLETE', 'UPDATE_COMPLETE']:
            return s3_dataset
        else:
            delete_s3_dataset(client, env['environmentUri'], s3_dataset.datasetUri)
            raise RuntimeError(f'failed to create {dataset_name=} {s3_dataset=}')


@pytest.fixture(scope='session')
def persistent_s3_dataset1(client1, group1, persistent_env1, testdata):
    return get_or_create_persistent_s3_dataset('persistent_s3_dataset1', client1, group1, persistent_env1)


@pytest.fixture(scope='session')
def persistent_imported_sse_s3_dataset1(client1, group1, persistent_env1, persistent_env1_aws_client, testdata):
    bucket_name = 'dataalltestingpersistentimportedsses3'
    bucket = None
    try:
        s3_client = S3Client(session=persistent_env1_aws_client, region=persistent_env1['region'])
        bucket = s3_client.bucket_exists(bucket_name)
        if not bucket:
            bucket = s3_client.create_bucket(bucket_name=bucket_name, kms_key_arn=None)
    except Exception as e:
        raise Exception(f'Error creating {bucket_name=} due to: {e}')
    return get_or_create_persistent_s3_dataset(
        'persistent_imported_sse_s3_dataset1', client1, group1, persistent_env1, bucket_name
    )


@pytest.fixture(scope='session')
def persistent_imported_kms_s3_dataset1(
    client1, group1, persistent_env1, persistent_env1_aws_client, persistent_env1_integration_role_arn, testdata
):
    resource_name = 'dataalltestingpersistentimportedkms'
    bucket = None
    kms_alias = None
    database = None
    existing_lf_admins = None
    try:
        # Check and create KMS key
        kms_client = KMSClient(
            session=persistent_env1_aws_client,
            account_id=persistent_env1['AwsAccountId'],
            region=persistent_env1['region'],
        )
        kms_id, kms_alias = kms_client.get_key_id_and_alias(resource_name)
        if not kms_id:
            kms_id, kms_alias = kms_client.create_key_with_alias(resource_name)
        # Check and create S3 Bucket
        s3_client = S3Client(session=persistent_env1_aws_client, region=persistent_env1['region'])
        bucket = s3_client.bucket_exists(resource_name)
        if not bucket:
            bucket = s3_client.create_bucket(
                bucket_name=resource_name,
                kms_key_arn=f"arn:aws:kms:{persistent_env1['region']}:{persistent_env1['AwsAccountId']}:key/{kms_id}",
            )
        # Check and create Glue database
        lf_client = LakeFormationClient(session=persistent_env1_aws_client, region=persistent_env1['region'])
        existing_lf_admins = lf_client.add_role_to_datalake_admin(role_arn=persistent_env1_integration_role_arn)
        if lf_client.grant_create_database(role_arn=persistent_env1_integration_role_arn):
            glue_client = GlueClient(session=persistent_env1_aws_client, region=persistent_env1['region'])
            database = glue_client.get_database(resource_name)
            if not database:
                database = glue_client.create_database(database_name=resource_name, bucket=bucket)
        if None in [bucket, database, kms_alias]:
            raise Exception('Error creating import dataset AWS resources for persistent_imported_kms_s3_dataset1')
    except Exception:
        if bucket:
            S3Client(session=persistent_env1_aws_client, region=persistent_env1['region']).delete_bucket(bucket)
        if kms_alias:
            KMSClient(
                session=persistent_env1_aws_client,
                account_id=persistent_env1['AwsAccountId'],
                region=persistent_env1['region'],
            ).delete_key_by_alias(kms_alias)
        if existing_lf_admins:
            LakeFormationClient(
                session=persistent_env1_aws_client, region=persistent_env1['region']
            ).remove_role_from_datalake_admin(existing_lf_admins)
        if database:
            GlueClient(session=persistent_env1_aws_client, region=persistent_env1['region']).delete_database(database)
        raise Exception('Error creating import dataset AWS resources for persistent_imported_sse_s3_dataset1')

    return get_or_create_persistent_s3_dataset(
        'persistent_imported_kms_s3_dataset1',
        client1,
        group1,
        persistent_env1,
        resource_name,
        resource_name,
        resource_name,
    )
