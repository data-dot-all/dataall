import { gql } from 'apollo-boost';

export const getShareLogs = (shareUri) => ({
  variables: {
    shareUri
  },
  query: gql`
    query getShareLogs($shareUri: String!) {
      getShareLogs(shareUri: $shareUri) {
        message
        timestamp
      }
    }
  `
});
