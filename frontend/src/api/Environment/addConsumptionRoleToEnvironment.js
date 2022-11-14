import { gql } from 'apollo-boost';

const addConsumptionRoleToEnvironment = (input) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation addConsumptionRoleToEnvironment($input: AddConsumptionRoleToEnvironmentInput!) {
      addConsumptionRoleToEnvironment(input: $input) {
        groupConsumptionRoleUri
        consumptionRoleName
        environmentUri
        groupUri
        IAMRoleArn
      }
    }
  `
});

export default addConsumptionRoleToEnvironment;
