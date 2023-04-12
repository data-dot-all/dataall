import { gql } from 'apollo-boost';

export const getSagemakerStudioUserProfilePresignedUrl = (
  sagemakerStudioUserProfileUri
) => ({
  variables: {
    sagemakerStudioUserProfileUri
  },
  query: gql`
    query getSagemakerStudioUserProfilePresignedUrl(
      $sagemakerStudioUserProfileUri: String!
    ) {
      getSagemakerStudioUserProfilePresignedUrl(
        sagemakerStudioUserProfileUri: $sagemakerStudioUserProfileUri
      )
    }
  `
});
