import { gql } from 'apollo-boost';

export const getStack = (environmentUri, stackUri, targetUri, targetType) => ({
  variables: {
    environmentUri,
    stackUri,
    targetUri,
    targetType
  },
  query: gql`
    query getStack(
      $environmentUri: String!
      $stackUri: String!
      $targetUri: String!
      $targetType: String!
    ) {
      getStack(
        environmentUri: $environmentUri
        stackUri: $stackUri
        targetUri: $targetUri
        targetType: $targetType
      ) {
        status
        stackUri
        targetUri
        accountid
        region
        stackid
        link
        outputs
        resources
        error
        events
        name
        canViewLogs
      }
    }
  `
});
