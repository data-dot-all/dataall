import { gql } from 'apollo-boost';

const removeConsumptionRoleFromEnvironment = ({ environmentUri, groupConsumptionRoleUri }) => ({
  variables: {
    environmentUri,
    groupConsumptionRoleUri
  },
  mutation: gql`
    mutation removeConsumptionRoleFromEnvironment(
      $environmentUri: String!
      $groupConsumptionRoleUri: String!
    ) {
      removeConsumptionRoleFromEnvironment(
        environmentUri: $environmentUri
        groupConsumptionRoleUri: $groupConsumptionRoleUri
      )
    }
  `
});

export default removeConsumptionRoleFromEnvironment;
