import { gql } from 'apollo-boost';

export const SearchResources = (filter) => ({
  variables: {
    filter
  },
  query: gql`
    query SearchResources($filter: SearchInputFilter) {
      searchResources(filter: $filter) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          objectUri
          objectType
          label
          description
          tags
        }
      }
    }
  `
});
