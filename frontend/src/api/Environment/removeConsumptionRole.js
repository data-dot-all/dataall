import { gql } from 'apollo-boost';

const removeConsumptionRoleFromEnvironment = ({ environmentUri, consumptionRoleUri }) => ({
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

export default removeConsumptionRoleFromEnvironment;
