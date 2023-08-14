import { gql } from 'apollo-boost';

export const inviteGroupOnEnvironment = (input) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation inviteGroupOnEnvironment($input: InviteGroupOnEnvironmentInput!) {
      inviteGroupOnEnvironment(input: $input) {
        environmentUri
      }
    }
  `
});
