import { gql } from 'apollo-boost';

const searchDatasets = ({ filters, page, term }) => ({
  variables: {
    filters,
    page: page || 1,
    term
  },
  query: gql`
    query SearchDatasets($filters: FacetFilters, $page: Int, $term: String) {
      searchDatasets(filters: $filters, page: $page, term: $term) {
        hits {
          count
          page
          pageSize
          hasNext
          hasPrevious
          pages
          nodes {
            datasetUri
            label
            owner
            userRoleForDataset
            created
            region
            description
            tags
            organization {
              label
              organizationUri
            }
            environment {
              label
            }
            statistics {
              tables
              locations
            }
          }
        }
        facets {
          groups {
            dimensionName
            items {
              value
              count
            }
          }
        }
      }
    }
  `
});

export default searchDatasets;
