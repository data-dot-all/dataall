import { gql } from 'apollo-boost';

export const updateUserRole = ({ organizationUri, userName, role }) => ({
  variables: {
    input: { organizationUri, userName, role: role || 'Member' }
  },
  mutation: gql`
    mutation UpdateUser($input: ModifyOrganizationUserInput) {
      updateUser(input: $input) {
        userName
        userRoleInOrganization
        created
      }
    }
  `
});
