import { gql } from 'apollo-boost';

export const getConsumptionRolePolicies = ({
  environmentUri,
  IAMRoleName
}) => ({
  variables: {
    environmentUri,
    IAMRoleName
  },
  query: gql`
    query getConsumptionRolePolicies(
      $environmentUri: String!
      $IAMRoleName: String!
    ) {
      getConsumptionRolePolicies(
        environmentUri: $environmentUri
        IAMRoleName: $IAMRoleName
      ) {
        policy_type
        policy_name
        attached
        exists
      }
    }
  `
});
