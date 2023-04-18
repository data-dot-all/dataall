import { gql } from 'apollo-boost';

export const updateGroupRoleInOrganization = ({ groupUri, role }) => ({
  variables: {
    input: { role: role || 'Member' },
    groupUri
  },
  mutation: gql`
    mutation UpdateGroup($groupUri: String, $input: ModifyGroupInput) {
      updateGroup(groupUri: $groupUri, input: $input) {
        groupUri
        groupRoleInOrganization
        userRoleInGroup
        created
        updated
      }
    }
  `
});
