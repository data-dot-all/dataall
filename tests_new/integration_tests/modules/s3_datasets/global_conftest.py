import logging

import pytest

from integration_tests.client import GqlError
from integration_tests.core.stack.utils import check_stack_ready

from integration_tests.modules.s3_datasets import (
    create_dataset,
    import_dataset,
    delete_dataset,
    update_dataset,
)

log = logging.getLogger(__name__)


def create_s3_dataset(client, owner, group, org_uri, env_uri, dataset_name, tags=[], autoApprovalEnabled = False, confidentiality = None):
    dataset = create_dataset(
        client, name=dataset_name, owner=owner, group=group, organizationUri=org_uri, environmentUri=env_uri, tags=tags, autoApprovalEnabled=autoApprovalEnabled, confidentiality=confidentiality
    )
    check_stack_ready(client, env_uri, dataset.stack.stackUri)
    return dataset #TODO get_dataset

def import_s3_dataset(client, owner, group, org_uri, env_uri, dataset_name, bucket, kms_alias, tags=[], autoApprovalEnabled = False, confidentiality = None):
    dataset = import_dataset(
        client, name=dataset_name, owner=owner, group=group, organizationUri=org_uri, environmentUri=env_uri, tags=tags, bucketName=bucket, KmsKeyAlias=kms_alias, autoApprovalEnabled=autoApprovalEnabled, confidentiality=confidentiality
    )
    check_stack_ready(client, env_uri, dataset.stack.stackUri)
    return dataset #TODO get_dataset

def delete_s3_dataset(client, env_uri, dataset):
    check_stack_ready(client, env_uri, dataset.stack.stackUri)
    try:
        return delete_dataset(client, dataset.datasetUri)
    except GqlError:
        log.exception('unexpected error when deleting dataset')
        return False


@pytest.fixture(scope='session')
def session_s3_dataset1(client1, group1, org1, session_env1, session_id, testdata):
    envdata = testdata.datasets['session_dataset1']
    ds = None
    try:
        ds = create_s3_dataset(client1, owner='someone', group=group1, org_uri=org1['organizationUri'], env_uri=session_env1['environmentUri'], dataset_name=envdata.name, tags=[session_id])
        yield ds
    finally:
        if ds:
            delete_s3_dataset(client1, session_env1['environmentUri'], ds)
