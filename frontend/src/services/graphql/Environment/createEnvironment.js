import { gql } from 'apollo-boost';

export const createEnvironment = (input) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation CreateEnvironment($input: NewEnvironmentInput) {
      createEnvironment(input: $input) {
        environmentUri
        label
        userRoleInEnvironment
        SamlGroupName
        AwsAccountId
        created
        dashboardsEnabled
        mlStudiosEnabled
        pipelinesEnabled
        warehousesEnabled
        parameters {
          key
          value
        }
      }
    }
  `
});
