import { gql } from 'apollo-boost';

const listEnvironmentConsumptionRoles = ({ filter, environmentUri }) => ({
  variables: {
    environmentUri,
    filter
  },
  query: gql`
    query listEnvironmentConsumptionRoles(
      $filter: ConsumptionRoleFilter
      $environmentUri: String!
    ) {
      listEnvironmentConsumptionRoles(
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

export default listEnvironmentConsumptionRoles;
