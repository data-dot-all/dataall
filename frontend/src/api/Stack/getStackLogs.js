import { gql } from 'apollo-boost';

export const getStackLogs = (environmentUri, stackUri) => ({
  variables: {
    environmentUri,
    stackUri
  },
  query: gql`
    query getStackLogs($environmentUri: String!, $stackUri: String!) {
      getStackLogs(environmentUri: $environmentUri, stackUri: $stackUri) {
        message
        timestamp
      }
    }
  `
});
