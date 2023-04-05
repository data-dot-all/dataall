import { gql } from 'apollo-boost';

export const listOrganizationTopics = ({ filter, organizationUri }) => ({
  variables: {
    organizationUri,
    filter
  },
  query: gql`
    query ListOrganizationTopics(
      $organizationUri: String
      $filter: OrganizationTopicFilter
    ) {
      listOrganizationTopics(
        organizationUri: $organizationUri
        filter: $filter
      ) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          label
          topicUri
          description
        }
      }
    }
  `
});
