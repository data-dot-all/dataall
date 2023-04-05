import { gql } from 'apollo-boost';

export const listEnvironmentGroupInvitationPermissions = ({
  environmentUri
}) => ({
  variables: {
    environmentUri
  },
  query: gql`
    query listEnvironmentGroupInvitationPermissions($environmentUri: String) {
      listEnvironmentGroupInvitationPermissions(
        environmentUri: $environmentUri
      ) {
        permissionUri
        name
        description
      }
    }
  `
});
