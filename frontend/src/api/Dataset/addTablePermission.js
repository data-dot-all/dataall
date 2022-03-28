import { gql } from 'apollo-boost';

const addTablePermissions = ({ tableUri, role, userName }) => ({
  variables: {
    tableUri,
    role,
    userName
  },
  mutation: gql`
    mutation AddTablePermission(
      $tableUri: String!
      $userName: String!
      $role: DatasetRole!
    ) {
      addTablePermission(
        tableUri: $tableUri
        userName: $userName
        role: $role
      ) {
        tableUri
      }
    }
  `
});

export default addTablePermissions;
