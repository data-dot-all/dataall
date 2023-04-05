import { gql } from 'apollo-boost';

export const getStack = (environmentUri, stackUri) => ({
  variables: {
    environmentUri,
    stackUri
  },
  query: gql`
    query getStack($environmentUri: String!, $stackUri: String!) {
      getStack(environmentUri: $environmentUri, stackUri: $stackUri) {
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
      }
    }
  `
});
