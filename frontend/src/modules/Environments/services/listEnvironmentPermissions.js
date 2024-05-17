import { gql } from 'apollo-boost';

export const listEnvironmentGroupInvitationPermissions = () => ({
  query: gql`
    query listEnvironmentGroupInvitationPermissions {
      listEnvironmentGroupInvitationPermissions {
        permissionUri
        name
        description
      }
    }
  `
});
