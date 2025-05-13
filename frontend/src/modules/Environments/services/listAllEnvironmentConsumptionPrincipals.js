import { gql } from 'apollo-boost';

export const listAllEnvironmentConsumptionPrincipals = ({
  filter,
  environmentUri
}) => ({
  variables: {
    environmentUri,
    filter
  },
  query: gql`
    query listAllEnvironmentConsumptionPrincipals(
      $filter: ConsumptionRoleFilter
      $environmentUri: String!
    ) {
      listAllEnvironmentConsumptionPrincipals(
        environmentUri: $environmentUri
        filter: $filter
      ) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          consumptionPrincipalUri
          consumptionPrincipalName
          environmentUri
          groupUri
          IAMPrincipalArn
          dataallManaged
          consumptionPrincipalType
        }
      }
    }
  `
});
