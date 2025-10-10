from assertpy import assert_that

from integration_tests.errors import GqlError

from integration_tests.modules.feed.queries import post_feed_message, get_feed


S3_DATASET_TARGET_TYPE = 'Dataset'


def test_get_feed(client1, session_s3_dataset1):
    feed = get_feed(client1, session_s3_dataset1.datasetUri, S3_DATASET_TARGET_TYPE)
    assert_that(feed).is_not_none()


def test_post_feed_message(client1, session_s3_dataset1, session_id):
    feed_message_count = get_feed(
        client1, session_s3_dataset1.datasetUri, S3_DATASET_TARGET_TYPE, filter={'term': session_id}
    ).messages.count

    feed_mesage = post_feed_message(client1, session_s3_dataset1.datasetUri, S3_DATASET_TARGET_TYPE, session_id)
    assert_that(feed_mesage.feedMessageUri).is_not_none()

    feed = get_feed(client1, session_s3_dataset1.datasetUri, S3_DATASET_TARGET_TYPE, filter={'term': session_id})
    assert_that(feed.messages.count).is_equal_to(feed_message_count + 1)
    assert_that(feed.messages.nodes[0].content).is_equal_to(session_id)


def test_post_feed_message_invalid(client1, session_s3_dataset1):
    assert_that(post_feed_message).raises(GqlError).when_called_with(
        client1, session_s3_dataset1.datasetUri, None, None
    ).contains('targetType', 'must not be null')
    assert_that(post_feed_message).raises(GqlError).when_called_with(
        client1, None, S3_DATASET_TARGET_TYPE, None
    ).contains('targetUri', 'must not be null')


def test_get_feed_invalid(client1, session_s3_dataset1):
    assert_that(get_feed).raises(GqlError).when_called_with(client1, session_s3_dataset1.datasetUri, None).contains(
        'targetType', 'must not be null'
    )
    assert_that(get_feed).raises(GqlError).when_called_with(client1, None, S3_DATASET_TARGET_TYPE).contains(
        'targetUri', 'must not be null'
    )


def test_post_feed_message_unauthorized(client2, session_s3_dataset1):
    assert_that(post_feed_message).raises(GqlError).when_called_with(
        client2, session_s3_dataset1.datasetUri, S3_DATASET_TARGET_TYPE, 'message'
    ).contains('UnauthorizedOperation', 'GET_DATASET', session_s3_dataset1.datasetUri)


def test_get_feed_unauthorized(client2, session_s3_dataset1):
    assert_that(get_feed).raises(GqlError).when_called_with(
        client2, session_s3_dataset1.datasetUri, S3_DATASET_TARGET_TYPE
    ).contains('UnauthorizedOperation', 'GET_DATASET', session_s3_dataset1.datasetUri)
