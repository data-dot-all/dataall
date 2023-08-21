import { gql } from 'apollo-boost';

export const inviteGroupToOrganization = (input) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation inviteGroupToOrganization(
      $input: InviteGroupToOrganizationInput!
    ) {
      inviteGroupToOrganization(input: $input) {
        organizationUri
      }
    }
  `
});
