import { gql } from 'apollo-boost';

const listAllEnvironmentConsumptionRoles = ({ filter, environmentUri }) => ({
  variables: {
    environmentUri,
    filter
  },
  query: gql`
    query listAllEnvironmentConsumptionRoles(
      $filter: GroupFilter
      $environmentUri: String!
    ) {
      listAllEnvironmentConsumptionRoles(
        environmentUri: $environmentUri
        filter: $filter
      ) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          groupConsumptionRoleUri
          consumptionRoleName
          environmentUri
          groupUri
          IAMRoleArn
        }
      }
    }
  `
});

export default listAllEnvironmentConsumptionRoles;
