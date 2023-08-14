import { gql } from 'apollo-boost';

export const listGlossaries = (filter) => ({
  variables: {
    filter
  },
  query: gql`
    query ListGlossaries($filter: GlossaryFilter) {
      listGlossaries(filter: $filter) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          nodeUri
          label
          readme
          created
          owner
          path
          status
          deleted
          admin
          stats {
            categories
            terms
            associations
          }
        }
      }
    }
  `
});
