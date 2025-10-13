# TODO: This file will be replaced by using the SDK directly


def upvote(client, uri, target_type, vote):
    query = {
        'operationName': 'upVote',
        'variables': {'input': {'targetUri': uri, 'targetType': target_type, 'upvote': vote}},
        'query': """
            mutation upVote($input:VoteInput!){
                upVote(input:$input){
                    voteUri
                    targetUri
                    targetType
                    upvote
                }
            }
                """,
    }

    response = client.query(query=query)
    return response.data.upVote


def count_upvotes(client, uri, target_type):
    query = {
        'operationName': 'countUpVotes',
        'variables': {'targetUri': uri, 'targetType': target_type},
        'query': """
            query countUpVotes($targetUri:String!, $targetType:String!){
                countUpVotes(targetUri:$targetUri, targetType:$targetType)
            }
                """,
    }
    response = client.query(query=query)
    return response.data.countUpVotes


def get_vote(client, uri, target_type):
    query = {
        'operationName': 'getVote',
        'variables': {'targetUri': uri, 'targetType': target_type},
        'query': """
            query getVote($targetUri:String!, $targetType:String!){
                getVote(targetUri:$targetUri, targetType:$targetType){
                upvote
                voteUri
                targetUri
                targetType
                }
            }
                """,
    }
    response = client.query(query=query)
    print(response.data.getVote)
    return response.data.getVote
