import { gql } from 'apollo-boost';

export const getVote = (targetUri, targetType) => ({
  variables: {
    targetUri,
    targetType
  },
  query: gql`
    query getVote($targetUri: String!, $targetType: String!) {
      getVote(targetUri: $targetUri, targetType: $targetType) {
        upvote
      }
    }
  `
});
