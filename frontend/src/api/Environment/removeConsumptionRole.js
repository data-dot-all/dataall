import { gql } from 'apollo-boost';

export const removeConsumptionRoleFromEnvironment = ({
  environmentUri,
  consumptionRoleUri
}) => ({
  variables: {
    environmentUri,
    consumptionRoleUri
  },
  mutation: gql`
    mutation removeConsumptionRoleFromEnvironment(
      $environmentUri: String!
      $consumptionRoleUri: String!
    ) {
      removeConsumptionRoleFromEnvironment(
        environmentUri: $environmentUri
        consumptionRoleUri: $consumptionRoleUri
      )
    }
  `
});
