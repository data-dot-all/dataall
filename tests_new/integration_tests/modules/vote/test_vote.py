from assertpy import assert_that

from integration_tests.errors import GqlError

from integration_tests.modules.vote.queries import upvote, count_upvotes, get_vote
from integration_tests.modules.vote.conftest import S3_DATASET_TARGET_TYPE


def test_upvote(client1, vote1):
    assert_that(vote1).is_not_none()
    assert_that(vote1.voteUri).is_not_none()
    assert_that(vote1.upvote).is_true()


def test_upvote_invalid(client1, vote1, session_s3_dataset1):
    assert_that(upvote).raises(GqlError).when_called_with(client1, session_s3_dataset1.datasetUri, None, True).contains(
        'targetType', 'not to be None'
    )
    assert_that(upvote).raises(GqlError).when_called_with(client1, None, S3_DATASET_TARGET_TYPE, True).contains(
        'targetUri', 'not to be None'
    )


def test_get_vote_invalid(client1, vote1, session_s3_dataset1):
    assert_that(get_vote).raises(GqlError).when_called_with(client1, session_s3_dataset1.datasetUri, None).contains(
        'targetType', 'must not be null'
    )
    assert_that(get_vote).raises(GqlError).when_called_with(client1, None, S3_DATASET_TARGET_TYPE).contains(
        'targetUri', 'must not be null'
    )


def test_count_upvote_invalid(client1, vote1, session_s3_dataset1):
    assert_that(count_upvotes).raises(GqlError).when_called_with(
        client1, session_s3_dataset1.datasetUri, None
    ).contains('targetType', 'must not be null')
    assert_that(count_upvotes).raises(GqlError).when_called_with(client1, None, S3_DATASET_TARGET_TYPE).contains(
        'targetUri', 'must not be null'
    )


def test_count_votes(client1, vote1, session_s3_dataset1):
    assert_that(count_upvotes(client1, session_s3_dataset1.datasetUri, S3_DATASET_TARGET_TYPE)).is_equal_to(1)
