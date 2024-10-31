import { gql } from 'apollo-boost';

export const addConnectionGroupPermission = (
  connectionUri,
  groupUri,
  permissions
) => ({
  variables: {
    connectionUri,
    groupUri,
    permissions
  },
  mutation: gql`
    mutation addConnectionGroupPermission(
      $connectionUri: String!
      $groupUri: String!
      $permissions: [String]!
    ) {
      addConnectionGroupPermission(
        connectionUri: $connectionUri
        groupUri: $groupUri
        permissions: $permissions
      )
    }
  `
});
