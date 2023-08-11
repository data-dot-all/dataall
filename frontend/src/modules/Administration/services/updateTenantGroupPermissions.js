import { gql } from 'apollo-boost';

export const updateTenantGroupPermissions = (input) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation updateGroupTenantPermissions(
      $input: UpdateGroupTenantPermissionsInput!
    ) {
      updateGroupTenantPermissions(input: $input)
    }
  `
});
