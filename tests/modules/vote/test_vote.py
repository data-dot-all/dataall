def count_votes_query(client, target_uri, target_type, group):
    response = client.query(
        """
        query countUpVotes($targetUri:String!, $targetType:String!){
            countUpVotes(targetUri:$targetUri, targetType:$targetType)
        }
        """,
        targetUri=target_uri,
        targetType=target_type,
        username='alice',
        groups=[group],
    )
    return response


def get_vote_query(client, target_uri, target_type, group):
    response = client.query(
        """
        query getVote($targetUri:String!, $targetType:String!){
            getVote(targetUri:$targetUri, targetType:$targetType){
             upvote
            }
        }
        """,
        targetUri=target_uri,
        targetType=target_type,
        username='alice',
        groups=[group],
    )
    return response


def upvote_mutation(client, target_uri, target_type, upvote, group):
    response = client.query(
        """
        mutation upVote($input:VoteInput!){
            upVote(input:$input){
                voteUri
                targetUri
                targetType
                upvote
            }
        }
        """,
        input=dict(
            targetUri=target_uri,
            targetType=target_type,
            upvote=upvote,
        ),
        username='alice',
        groups=[group],
    )
    return response
