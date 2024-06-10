import { gql } from 'apollo-boost';

export const listEnvironmentConsumptionRoles = ({
  filter,
  environmentUri
}) => ({
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
          IAMRoleName
          dataallManaged
        }
      }
    }
  `
});
