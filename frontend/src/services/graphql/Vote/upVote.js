import { gql } from 'apollo-boost';

export const upVote = (input) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation upVote($input: VoteInput!) {
      upVote(input: $input) {
        voteUri
        targetUri
        targetType
        upvote
      }
    }
  `
});
