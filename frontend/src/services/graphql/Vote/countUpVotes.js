import { gql } from 'apollo-boost';

export const countUpVotes = (targetUri, targetType) => ({
  variables: {
    targetUri,
    targetType
  },
  query: gql`
    query countUpVotes($targetUri: String!, $targetType: String!) {
      countUpVotes(targetUri: $targetUri, targetType: $targetType)
    }
  `
});
