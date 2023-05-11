import { gql } from 'apollo-boost';

const deleteSagemakerStudioUser = (
  sagemakerStudioUserUri,
  deleteFromAWS
) => ({
  variables: {
    sagemakerStudioUserUri,
    deleteFromAWS
  },
  mutation: gql`
    mutation deleteSagemakerStudioUser(
      $sagemakerStudioUserUri: String!
      $deleteFromAWS: Boolean
    ) {
      deleteSagemakerStudioUser(
        sagemakerStudioUserUri: $sagemakerStudioUserUri
        deleteFromAWS: $deleteFromAWS
      )
    }
  `
});

export default deleteSagemakerStudioUser;
