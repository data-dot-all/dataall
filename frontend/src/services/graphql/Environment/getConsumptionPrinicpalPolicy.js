import { gql } from 'apollo-boost';

export const getConsumptionPrincipalPolicies = ({
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
    query getConsumptionPrincipalPolicies(
      $environmentUri: String!
      $IAMPrincipalName: String!
      $IAMPrincipalType: String!
    ) {
      getConsumptionPrincipalPolicies(
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
