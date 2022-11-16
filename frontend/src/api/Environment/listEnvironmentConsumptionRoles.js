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
      listEnvironmentConsumptionRoles(environmentUri: $environmentUri, filter: $filter) {
        {
          value
          label
        }
      }
    }
  `
});

export default listEnvironmentConsumptionRoles;
