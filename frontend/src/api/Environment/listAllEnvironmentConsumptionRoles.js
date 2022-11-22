import { gql } from 'apollo-boost';

const listAllEnvironmentConsumptionRoles = ({ filter, environmentUri }) => ({
  variables: {
    environmentUri,
    filter
  },
  query: gql`
    query listAllEnvironmentConsumptionRoles(
      $filter: ConsumptionRoleFilter
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
          consumptionRoleUri
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
