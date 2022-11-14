import { gql } from 'apollo-boost';

const removeConsumptionRoleFromEnvironment = ({ environmentUri, groupUri }) => ({
  variables: {
    environmentUri,
    groupUri
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
