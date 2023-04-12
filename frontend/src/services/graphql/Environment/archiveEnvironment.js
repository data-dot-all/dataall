import { gql } from 'apollo-boost';

export const archiveEnvironment = ({ environmentUri, deleteFromAWS }) => ({
  variables: {
    environmentUri,
    deleteFromAWS
  },
  mutation: gql`
    mutation deleteEnvironment(
      $environmentUri: String!
      $deleteFromAWS: Boolean
    ) {
      deleteEnvironment(
        environmentUri: $environmentUri
        deleteFromAWS: $deleteFromAWS
      )
    }
  `
});
