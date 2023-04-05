import { gql } from 'apollo-boost';

export const updateGroupEnvironmentPermissions = (input) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation updateGroupEnvironmentPermissions(
      $input: InviteGroupOnEnvironmentInput!
    ) {
      updateGroupEnvironmentPermissions(input: $input) {
        environmentUri
      }
    }
  `
});
