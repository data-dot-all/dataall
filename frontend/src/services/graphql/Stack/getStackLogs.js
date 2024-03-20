import { gql } from 'apollo-boost';

export const getStackLogs = (stackUri) => ({
  variables: {
    stackUri
  },
  query: gql`
    query getStackLogs($stackUri: String!) {
      getStackLogs(stackUri: $stackUri) {
        message
        timestamp
      }
    }
  `
});
