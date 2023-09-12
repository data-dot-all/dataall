import { gql } from 'apollo-boost';

export const listOrganizationGroups = ({ filter, organizationUri }) => ({
  variables: {
    organizationUri,
    filter
  },
  query: gql`
    query listOrganizationGroups(
      $filter: GroupFilter
      $organizationUri: String!
    ) {
      listOrganizationGroups(
        organizationUri: $organizationUri
        filter: $filter
      ) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          groupUri
          invitedBy
          created
        }
      }
    }
  `
});
