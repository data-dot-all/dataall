import { gql } from 'apollo-boost';

const inviteGroupToOrganization = (input) => ({
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

export default inviteGroupToOrganization;
