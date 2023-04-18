import { gql } from 'apollo-boost';

export const removeTablePermissions = ({ tableUri, role, userName }) => ({
  variables: {
    tableUri,
    role,
    userName
  },
  mutation: gql`
    mutation RemoveTablePermission($tableUri: String!, $userName: String!) {
      removeTablePermission(tableUri: $tableUri, userName: $userName)
    }
  `
});
