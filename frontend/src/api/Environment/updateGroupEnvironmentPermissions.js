import { gql } from 'apollo-boost';

const updateGroupEnvironmentPermissions = (input) => ({
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

export default updateGroupEnvironmentPermissions;
