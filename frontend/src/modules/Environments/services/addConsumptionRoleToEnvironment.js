import { gql } from 'apollo-boost';

export const addConsumptionRoleToEnvironment = (input) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation addConsumptionRoleToEnvironment(
      $input: AddConsumptionRoleToEnvironmentInput!
    ) {
      addConsumptionRoleToEnvironment(input: $input) {
        consumptionPrincipalUri
        consumptionPrincipalName
        environmentUri
        groupUri
        IAMPrincipalArn
      }
    }
  `
});
