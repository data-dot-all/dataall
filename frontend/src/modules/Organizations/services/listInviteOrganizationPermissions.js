import { gql } from 'apollo-boost';

export const listInviteOrganizationPermissionsWithDescriptions = () => ({
  query: gql`
    query listInviteOrganizationPermissionsWithDescriptions {
      listInviteOrganizationPermissionsWithDescriptions {
        name
        description
      }
    }
  `
});
