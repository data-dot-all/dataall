import { gql } from 'apollo-boost';

export const getStackLogs = (targetUri, targetType) => ({
  variables: {
    targetUri,
    targetType
  },
  query: gql`
    query getStackLogs($targetUri: String!, $targetType: String!) {
      getStackLogs(targetUri: $targetUri, targetType: $targetType) {
        message
        timestamp
      }
    }
  `
});
