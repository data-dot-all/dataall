from tests.api.conftest import *
from tests.api.client import *

class FeedTestHelper:

    def __init__(self, test_object_fixture, client_fixture):
        self._test_object_fixture = test_object_fixture
        self._client_fixture = client_fixture

    def test_post_message(self, object_name, uri):
        response = self._client_fixture.query(
            """
                mutation PostFeedMessage(
                    $targetUri : String!,
                    $targetType: String!,
                    $input:FeedMessageInput
                ){
                    postFeedMessage(targetUri:$targetUri, targetType:$targetType,input:$input){
                        feedMessageUri
                        content
                        created
                        creator
                    }
                }
            """,
            username='me',
            targetUri=getattr(self._test_object_fixture, uri),
            targetType=object_name,
            input={'content': 'hello'},
        )

        assert response.data.postFeedMessage.content == 'hello'
        assert response.data.postFeedMessage.creator == 'me'

    def test_list_messages(self, object_name, uri):
        response = self._client_fixture.query(
            """
            query GetFeed(
                $targetUri:String!,
                $targetType:String!,
                $filter:FeedMessageFilter!
            ){
                getFeed(
                    targetUri:$targetUri,
                    targetType:$targetType,

                ){
                    messages( filter:$filter){
                        count
                        page
                        pages
                        hasNext
                        hasPrevious
                        nodes{
                            content
                            created
                        }
                    }
                }
            }
            """,
            username='me',
            targetUri=getattr(self._test_object_fixture, uri),
            targetType=object_name,
            filter={},
        )

        assert response.data.getFeed.messages.count == 1
        assert response.data.getFeed.messages.nodes[0].content == 'hello'

    def test_get_target(self, object_name, uri):
        query_request = """
            query GetFeed(
                $targetUri:String!,
                $targetType:String!,
            ){
                getFeed(
                    targetUri:$targetUri,
                    targetType:$targetType,

                ){

                    target{
                        ... on """ + object_name + """{
                            """ + uri + """
                        }
                    }
                }
            }
            """

        response = self._client_fixture.query(
            query_request,
            targetUri=getattr(self._test_object_fixture, uri),
            targetType=object_name,
            username='me',
        )
        assert getattr(response.data.getFeed.target, uri) == getattr(self._test_object_fixture, uri)