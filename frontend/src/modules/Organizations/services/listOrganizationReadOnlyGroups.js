import { gql } from 'apollo-boost';

export const listOrganizationReadOnlyGroups = ({
  filter,
  organizationUri
}) => ({
  variables: {
    organizationUri,
    filter
  },
  query: gql`
    query listOrganizationReadOnlyGroups(
      $filter: GroupFilter
      $organizationUri: String!
    ) {
      listOrganizationReadOnlyGroups(
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
        }
      }
    }
  `
});
