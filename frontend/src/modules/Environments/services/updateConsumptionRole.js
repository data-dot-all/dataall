import { gql } from 'apollo-boost';

export const updateConsumptionRole = ({
  environmentUri,
  consumptionPrincipalUri,
  input
}) => ({
  variables: {
    environmentUri,
    consumptionPrincipalUri,
    input
  },
  mutation: gql`
    mutation updateConsumptionRole(
      $environmentUri: String!
      $consumptionPrincipalUri: String!
      $input: UpdateConsumptionRoleInput!
    ) {
      updateConsumptionRole(
        environmentUri: $environmentUri
        consumptionPrincipalUri: $consumptionPrincipalUri
        input: $input
      ) {
        consumptionPrincipalUri
        consumptionPrincipalName
        environmentUri
        groupUri
        IAMPrincipalName
        IAMPrincipalArn
      }
    }
  `
});
