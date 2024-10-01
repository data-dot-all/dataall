# TODO: This file will be replaced by using the SDK directly


def post_feed_message(client, target_uri, target_type, content):
    query = {
        'operationName': 'PostFeedMessage',
        'variables': {
            'targetUri': target_uri,
            'targetType': target_type,
            'input': {'content': content},
        },
        'query': """
            mutation PostFeedMessage(
              $targetUri: String!
              $targetType: String!
              $input: FeedMessageInput!
            ) {
              postFeedMessage(
                targetUri: $targetUri
                targetType: $targetType
                input: $input
              ) {
                feedMessageUri
                content
                created
                creator
              }
            }
                """,
    }
    response = client.query(query=query)
    return response.data.postFeedMessage


def get_feed(client, target_uri, target_type, filter={}):
    query = {
        'operationName': 'GetFeed',
        'variables': {'targetUri': target_uri, 'targetType': target_type, 'filter': filter},
        'query': """
            query GetFeed(
              $targetUri: String!
              $targetType: String!
              $filter: FeedMessageFilter
            ) {
              getFeed(targetUri: $targetUri, targetType: $targetType) {
                messages(filter: $filter) {
                  count
                  hasNext
                  hasPrevious
                  page
                  pages
                  nodes {
                    content
                    feedMessageUri
                    creator
                    created
                  }
                }
              }
            }
                """,
    }
    response = client.query(query=query)
    return response.data.getFeed
