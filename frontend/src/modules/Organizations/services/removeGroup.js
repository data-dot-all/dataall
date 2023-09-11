import { gql } from 'apollo-boost';

export const removeGroupFromOrganization = ({ organizationUri, groupUri }) => ({
  variables: {
    organizationUri,
    groupUri
  },
  mutation: gql`
    mutation removeGroupFromOrganization(
      $organizationUri: String!
      $groupUri: String!
    ) {
      removeGroupFromOrganization(
        organizationUri: $organizationUri
        groupUri: $groupUri
      ) {
        organizationUri
      }
    }
  `
});
