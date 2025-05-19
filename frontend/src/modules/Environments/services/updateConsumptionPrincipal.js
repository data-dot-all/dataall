import { gql } from 'apollo-boost';

export const updateConsumptionPrincipal = ({
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
    mutation updateConsumptionPrincipal(
      $environmentUri: String!
      $consumptionPrincipalUri: String!
      $input: UpdateConsumptionPrincipalInput!
    ) {
      updateConsumptionPrincipal(
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
