import { gql } from 'apollo-boost';

export const listAllConsumptionRoles = ({ filter }) => ({
  variables: {
    filter
  },
  query: gql`
    query listAllConsumptionRoles($filter: ConsumptionRoleFilter) {
      listAllConsumptionRoles(filter: $filter) {
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
        }
      }
    }
  `
});
