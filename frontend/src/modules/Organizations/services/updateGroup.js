import { gql } from 'apollo-boost';

export const updateOrganizationGroup = (input) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation updateOrganizationGroup($input: InviteGroupToOrganizationInput!) {
      updateOrganizationGroup(input: $input) {
        organizationUri
      }
    }
  `
});
