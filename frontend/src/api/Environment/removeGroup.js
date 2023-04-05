import { gql } from 'apollo-boost';

export const removeGroupFromEnvironment = ({ environmentUri, groupUri }) => ({
  variables: {
    environmentUri,
    groupUri
  },
  mutation: gql`
    mutation removeGroupFromEnvironment(
      $environmentUri: String!
      $groupUri: String!
    ) {
      removeGroupFromEnvironment(
        environmentUri: $environmentUri
        groupUri: $groupUri
      ) {
        environmentUri
      }
    }
  `
});
