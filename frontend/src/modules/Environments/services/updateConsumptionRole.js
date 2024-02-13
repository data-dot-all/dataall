import { gql } from 'apollo-boost';

export const updateConsumptionRole = ({
  environmentUri,
  consumptionRoleUri,
  input
}) => ({
  variables: {
    environmentUri,
    consumptionRoleUri,
    input
  },
  mutation: gql`
    mutation updateConsumptionRole(
      $environmentUri: String!
      $consumptionRoleUri: String!
      $input: UpdateConsumptionRoleInput!
    ) {
      updateConsumptionRole(
        environmentUri: $environmentUri
        consumptionRoleUri: $consumptionRoleUri
        input: $input
      ) {
        consumptionRoleUri
        consumptionRoleName
        environmentUri
        groupUri
        IAMRoleName
        IAMRoleArn
      }
    }
  `
});
