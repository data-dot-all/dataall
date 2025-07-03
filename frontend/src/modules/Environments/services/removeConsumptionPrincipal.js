import { gql } from 'apollo-boost';

export const removeConsumptionPrincipalFromEnvironment = ({
  environmentUri,
  consumptionPrincipalUri
}) => ({
  variables: {
    environmentUri,
    consumptionPrincipalUri
  },
  mutation: gql`
    mutation removeConsumptionPrincipalFromEnvironment(
      $environmentUri: String!
      $consumptionPrincipalUri: String!
    ) {
      removeConsumptionPrincipalFromEnvironment(
        environmentUri: $environmentUri
        consumptionPrincipalUri: $consumptionPrincipalUri
      )
    }
  `
});
