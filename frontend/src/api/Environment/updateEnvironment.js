import { gql } from 'apollo-boost';

const updateEnvironment = ({ environmentUri, input }) => ({
  variables: {
    environmentUri,
    input
  },
  mutation: gql`
    mutation UpdateEnvironment(
      $environmentUri: String!
      $input: ModifyEnvironmentInput
    ) {
      updateEnvironment(environmentUri: $environmentUri, input: $input) {
        environmentUri
        label
        userRoleInEnvironment
        SamlGroupName
        AwsAccountId
        mlStudiosEnabled
        pipelinesEnabled
        warehousesEnabled
        created
        parameters {
          key
          value
        }
      }
    }
  `
});

export default updateEnvironment;
