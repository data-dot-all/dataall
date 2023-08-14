import { gql } from 'apollo-boost';

export const listAllEnvironmentGroups = ({ filter, environmentUri }) => ({
  variables: {
    environmentUri,
    filter
  },
  query: gql`
    query listAllEnvironmentGroups(
      $filter: GroupFilter
      $environmentUri: String!
    ) {
      listAllEnvironmentGroups(
        environmentUri: $environmentUri
        filter: $filter
      ) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          groupUri
          invitedBy
          created
          description
          environmentIAMRoleArn
          environmentIAMRoleName
          environmentAthenaWorkGroup
          environmentPermissions(environmentUri: $environmentUri) {
            name
            permissionUri
          }
        }
      }
    }
  `
});
