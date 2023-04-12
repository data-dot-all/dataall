import { gql } from 'apollo-boost';

export const listOrganizationEnvironmentGroups = ({
  term,
  organizationUri
}) => ({
  variables: {
    organizationUri,
    filter: { term: term || '' }
  },
  query: gql`
    query getOrg($organizationUri: String, $filter: GroupFilter) {
      getOrganization(organizationUri: $organizationUri) {
        groups(filter: $filter) {
          count
          nodes {
            groupUri
            label
            created
            groupRoleInOrganization
            userRoleInGroup
          }
        }
      }
    }
  `
});
