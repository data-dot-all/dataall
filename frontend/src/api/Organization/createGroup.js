import { gql } from 'apollo-boost';

export const createGroup = ({ organizationUri, description, label, role }) => ({
  variables: {
    input: { organizationUri, description, label, role: role || 'Member' }
  },
  mutation: gql`
    mutation CreateGroup($input: NewGroupInput) {
      createGroup(input: $input) {
        groupUri
        label
        groupRoleInOrganization
        created
        userRoleInGroup
      }
    }
  `
});
