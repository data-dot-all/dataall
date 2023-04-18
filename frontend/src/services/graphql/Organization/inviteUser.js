import { gql } from 'apollo-boost';

export const inviteUser = ({ organizationUri, userName, role }) => ({
  variables: {
    input: { organizationUri, userName, role: role || 'Member' }
  },
  mutation: gql`
    mutation InviteUser($input: NewOrganizationUserInput) {
      inviteUser(input: $input) {
        userName
        userRoleInOrganization
        created
      }
    }
  `
});
