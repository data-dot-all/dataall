import { gql } from 'apollo-boost';

export const updateOrganization = ({ organizationUri, input }) => ({
  variables: {
    organizationUri,
    input
  },
  mutation: gql`
    mutation UpdateOrg(
      $organizationUri: String!
      $input: ModifyOrganizationInput!
    ) {
      updateOrganization(organizationUri: $organizationUri, input: $input) {
        organizationUri
        label
        created
      }
    }
  `
});
