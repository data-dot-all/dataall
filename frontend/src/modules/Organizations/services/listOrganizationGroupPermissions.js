import { gql } from 'apollo-boost';

export const listOrganizationGroupPermissions = ({
  organizationUri,
  groupUri
}) => ({
  variables: {
    organizationUri,
    groupUri
  },
  query: gql`
    query listOrganizationGroupPermissions(
      $organizationUri: String!
      $groupUri: String!
    ) {
      listOrganizationGroupPermissions(
        organizationUri: $organizationUri
        groupUri: $groupUri
      ) {
        name
      }
    }
  `
});
