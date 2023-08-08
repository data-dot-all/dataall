import { gql } from 'apollo-boost';

export const removeUserFromEnvironment = ({ environmentUri, userName }) => ({
  variables: { environmentUri, userName },
  mutation: gql`
    mutation RemoveUserFromEnvironment(
      $environmentUri: String!
      $userName: String!
    ) {
      removeUserFromEnvironment(
        environmentUri: $environmentUri
        userName: $userName
      )
    }
  `
});
