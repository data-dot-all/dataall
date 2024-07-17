import { gql } from 'apollo-boost';

export const listRedshiftDatasetTables = ({ datasetUri, filter }) => ({
  variables: {
    datasetUri,
    filter
  },
  query: gql`
    query listRedshiftDatasetTables(
      $datasetUri: String!
      $filter: RedshiftDatasetTableFilter
    ) {
      listRedshiftDatasetTables(datasetUri: $datasetUri, filter: $filter) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          rsTableUri
          datasetUri
          name
          label
          created
          description
        }
      }
    }
  `
});
