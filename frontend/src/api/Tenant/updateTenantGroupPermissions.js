import { gql } from 'apollo-boost';

const removeTenantAdministrator = (input) => ({
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

export default removeTenantAdministrator;
