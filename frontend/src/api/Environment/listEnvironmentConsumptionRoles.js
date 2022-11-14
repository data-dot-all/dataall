import { gql } from 'apollo-boost';

const listEnvironmentConsumptionRoles = ({ filter, environmentUri }) => ({
  variables: {
    environmentUri,
    filter
  },
  query: gql`
    query listEnvironmentConsumptionRoles(
      $filter: GroupFilter
      $environmentUri: String!
    ) {
      listEnvironmentConsumptionRoles(environmentUri: $environmentUri, filter: $filter) {
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

export default listEnvironmentConsumptionRoles;
