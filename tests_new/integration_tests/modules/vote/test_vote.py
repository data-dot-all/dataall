from assertpy import assert_that

from integration_tests.modules.vote.queries import upvote, count_upvotes
from integration_tests.modules.vote.conftest import S3_DATASET_TARGET_TYPE


def test_upvote(client1, vote1):
    assert_that(vote1).is_not_none()
    assert_that(vote1.voteUri).is_not_none()
    assert_that(vote1.upvote).is_true()


def test_count_votes(client2, vote1, persistent_s3_dataset1):
    count = count_upvotes(client2, persistent_s3_dataset1.datasetUri, S3_DATASET_TARGET_TYPE)

    # Assert incremeent by 1
    upvote(client2, persistent_s3_dataset1.datasetUri, S3_DATASET_TARGET_TYPE, True)
    assert_that(count_upvotes(client2, persistent_s3_dataset1.datasetUri, S3_DATASET_TARGET_TYPE)).is_equal_to(
        count + 1
    )

    # Assert decrement by 1
    upvote(client2, persistent_s3_dataset1.datasetUri, S3_DATASET_TARGET_TYPE, False)
    assert_that(count_upvotes(client2, persistent_s3_dataset1.datasetUri, S3_DATASET_TARGET_TYPE)).is_equal_to(count)
