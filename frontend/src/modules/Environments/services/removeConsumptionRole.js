import { gql } from 'apollo-boost';

export const removeConsumptionRoleFromEnvironment = ({
  environmentUri,
  consumptionPrincipalUri
}) => ({
  variables: {
    environmentUri,
    consumptionPrincipalUri
  },
  mutation: gql`
    mutation removeConsumptionRoleFromEnvironment(
      $environmentUri: String!
      $consumptionPrincipalUri: String!
    ) {
      removeConsumptionRoleFromEnvironment(
        environmentUri: $environmentUri
        consumptionRoleUri: $consumptionPrincipalUri
      )
    }
  `
});
