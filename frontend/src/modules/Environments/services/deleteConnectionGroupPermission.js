import { gql } from 'apollo-boost';

export const deleteConnectionGroupPermission = (connectionUri, groupUri) => ({
  variables: {
    connectionUri,
    groupUri
  },
  mutation: gql`
    mutation deleteConnectionGroupPermission(
      $connectionUri: String!
      $groupUri: String!
    ) {
      deleteConnectionGroupPermission(
        connectionUri: $connectionUri
        groupUri: $groupUri
      )
    }
  `
});
