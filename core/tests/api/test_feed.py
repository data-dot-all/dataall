import pytest

from dataall.db import models


@pytest.fixture(scope='module', autouse=True)
def worksheet(db):
    with db.scoped_session() as session:
        w = models.Worksheet(
            owner='me',
            label='xxx',
            SamlAdminGroupName='g',
        )
        session.add(w)
    return w


def test_post_message(client, worksheet):
    response = client.query(
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
        targetUri=worksheet.worksheetUri,
        targetType='Worksheet',
        input={'content': 'hello'},
    )

    assert response.data.postFeedMessage.content == 'hello'
    assert response.data.postFeedMessage.creator == 'me'


def test_list_messages(client, worksheet):
    response = client.query(
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
        targetUri=worksheet.worksheetUri,
        targetType='Worksheet',
        filter={},
    )

    assert response.data.getFeed.messages.count == 1
    assert response.data.getFeed.messages.nodes[0].content == 'hello'


def test_get_target(client, worksheet):
    response = client.query(
        """
        query GetFeed(
            $targetUri:String!,
            $targetType:String!,
        ){
            getFeed(
                targetUri:$targetUri,
                targetType:$targetType,

            ){

                target{
                    ... on Worksheet{
                        worksheetUri
                    }
                }
            }
        }
        """,
        targetUri=worksheet.worksheetUri,
        targetType='Worksheet',
        username='me',
    )
    print(response)
