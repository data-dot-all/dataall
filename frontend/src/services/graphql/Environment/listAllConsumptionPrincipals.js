import { gql } from 'apollo-boost';

export const listAllConsumptionPrincipals = ({ filter }) => ({
  variables: {
    filter
  },
  query: gql`
    query listAllConsumptionPrincipals($filter: ConsumptionPrincipalFilter) {
      listAllConsumptionPrincipals(filter: $filter) {
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
        }
      }
    }
  `
});
