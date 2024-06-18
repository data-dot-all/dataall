import { gql } from 'apollo-boost';

export const updateEnvironment = ({ environmentUri, input }) => ({
  variables: {
    environmentUri,
    input
  },
  mutation: gql`
    mutation UpdateEnvironment(
      $environmentUri: String!
      $input: ModifyEnvironmentInput!
    ) {
      updateEnvironment(environmentUri: $environmentUri, input: $input) {
        environmentUri
        label
        userRoleInEnvironment
        SamlGroupName
        AwsAccountId
        created
        parameters {
          key
          value
        }
      }
    }
  `
});
