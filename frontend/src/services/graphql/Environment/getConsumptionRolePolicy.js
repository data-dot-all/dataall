import { gql } from 'apollo-boost';

export const getConsumptionRolePolicies = ({
  environmentUri,
  IAMPrincipalName,
  IAMPrincipalType
}) => ({
  variables: {
    environmentUri,
    IAMPrincipalName,
    IAMPrincipalType
  },
  query: gql`
    query getConsumptionRolePolicies(
      $environmentUri: String!
      $IAMPrincipalName: String!
      $IAMPrincipalType: String!
    ) {
      getConsumptionRolePolicies(
        environmentUri: $environmentUri
        IAMPrincipalName: $IAMPrincipalName
        IAMPrincipalType: $IAMPrincipalType
      ) {
        policy_type
        policy_name
        attached
        exists
      }
    }
  `
});
