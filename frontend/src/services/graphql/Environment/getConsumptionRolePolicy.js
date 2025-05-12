import { gql } from 'apollo-boost';

export const getConsumptionRolePolicies = ({
  environmentUri,
  IAMPrincipalName
}) => ({
  variables: {
    environmentUri,
    IAMPrincipalName
  },
  query: gql`
    query getConsumptionRolePolicies(
      $environmentUri: String!
      $IAMPrincipalName: String!
    ) {
      getConsumptionRolePolicies(
        environmentUri: $environmentUri
        IAMPrincipalName: $IAMPrincipalName
      ) {
        policy_type
        policy_name
        attached
        exists
      }
    }
  `
});
