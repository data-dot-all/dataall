import pytest
from integration_tests.modules.vote.queries import upvote, get_vote


S3_DATASET_TARGET_TYPE = 'dataset'


@pytest.fixture(scope='session')
def vote1(client1, session_s3_dataset1):
    upvote(client1, session_s3_dataset1.datasetUri, S3_DATASET_TARGET_TYPE, True)
    yield get_vote(client1, session_s3_dataset1.datasetUri, S3_DATASET_TARGET_TYPE)
