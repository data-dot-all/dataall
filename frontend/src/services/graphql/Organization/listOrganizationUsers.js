import { gql } from 'apollo-boost';

export const listOrganizationUsers = ({ filter, organizationUri }) => {
  return {
    variables: {
      organizationUri,
      filter
    },
    query: gql`
      query getOrg($organizationUri: String, $filter: OrganizationUserFilter) {
        getOrganization(organizationUri: $organizationUri) {
          organizationUri
          label
          userRoleInOrganization
          users(filter: $filter) {
            count
            page
            pageSize
            pages
            hasNext
            hasPrevious
            nodes {
              userName
              created
              userRoleInOrganization
            }
          }
        }
      }
    `
  };
};
