import { gql } from 'apollo-boost';

export const createOrganization = (input) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation CreateOrg($input: NewOrganizationInput) {
      createOrganization(input: $input) {
        organizationUri
        label
        created
      }
    }
  `
});
