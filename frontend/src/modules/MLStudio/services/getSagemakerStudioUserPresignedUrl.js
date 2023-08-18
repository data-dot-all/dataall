import { gql } from 'apollo-boost';

export const getSagemakerStudioUserPresignedUrl = (sagemakerStudioUserUri) => ({
  variables: {
    sagemakerStudioUserUri
  },
  query: gql`
    query getSagemakerStudioUserPresignedUrl($sagemakerStudioUserUri: String!) {
      getSagemakerStudioUserPresignedUrl(
        sagemakerStudioUserUri: $sagemakerStudioUserUri
      )
    }
  `
});
