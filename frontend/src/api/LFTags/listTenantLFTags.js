import { gql } from 'apollo-boost';

const listTenantLFTags = (filter) => ({
  variables: {
    filter
  },
  query: gql`
    query listTenantLFTags($filter: LFTagFilter) {
      listTenantLFTags(filter: $filter) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          lftagUri
          LFTagKey
          LFTagValues
          description
        }
      }
    }
  `
});

export default listTenantLFTags;
