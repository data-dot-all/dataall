import { gql } from 'apollo-boost';

export const listEnvironmentConsumptionPrincipals = ({
  filter,
  environmentUri
}) => ({
  variables: {
    environmentUri,
    filter
  },
  query: gql`
    query listEnvironmentConsumptionPrincipals(
      $filter: ConsumptionPrincipalFilter
      $environmentUri: String!
    ) {
      listEnvironmentConsumptionPrincipals(
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
          IAMPrincipalName
          dataallManaged
          consumptionPrincipalType
        }
      }
    }
  `
});
