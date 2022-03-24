import { gql } from 'apollo-boost';

const upVote = (input) => ({
  variables: {
    input
  },
  mutation: gql`mutation upVote($input:VoteInput!){
            upVote(input:$input){
                voteUri
                targetUri
                targetType
                upvote
            }
        }`
});

export default upVote;
