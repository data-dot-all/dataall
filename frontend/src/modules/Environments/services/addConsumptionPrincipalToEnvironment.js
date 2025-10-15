import { gql } from 'apollo-boost';

export const addConsumptionPrincipalToEnvironment = (input) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation addConsumptionPrincipalToEnvironment(
      $input: AddConsumptionPrincipalToEnvironmentInput!
    ) {
      addConsumptionPrincipalToEnvironment(input: $input) {
        consumptionPrincipalUri
        consumptionPrincipalName
        environmentUri
        groupUri
        IAMPrincipalArn
      }
    }
  `
});
