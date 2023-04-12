import { gql } from 'apollo-boost';

export const deleteSagemakerStudioUserProfile = (
  sagemakerStudioUserProfileUri,
  deleteFromAWS
) => ({
  variables: {
    sagemakerStudioUserProfileUri,
    deleteFromAWS
  },
  mutation: gql`
    mutation deleteSagemakerStudioUserProfile(
      $sagemakerStudioUserProfileUri: String!
      $deleteFromAWS: Boolean
    ) {
      deleteSagemakerStudioUserProfile(
        sagemakerStudioUserProfileUri: $sagemakerStudioUserProfileUri
        deleteFromAWS: $deleteFromAWS
      )
    }
  `
});
