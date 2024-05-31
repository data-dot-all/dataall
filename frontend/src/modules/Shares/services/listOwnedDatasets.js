import { gql } from 'apollo-boost';

export const listOwnedDatasets = ({ filter }) => ({
  variables: {
    filter
  },
  query: gql`
    query listOwnedDatasets($filter: DatasetFilter) {
      listOwnedDatasets(filter: $filter) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          datasetUri
          label
        }
      }
    }
  `
});
