import { gql } from 'apollo-boost';

export const listRedshiftDatasetTables = ({ datasetUri, filter }) => ({
  variables: {
    datasetUri,
    filter
  },
  query: gql`
    query listRedshiftDatasetTables(
      $datasetUri: String!
      $filter: DatasetTableFilter
    ) {
      listRedshiftDatasetTables(datasetUri: $datasetUri, filter: $filter) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          tableUri
          name
          created
          description
          userRoleForTable
        }
      }
    }
  `
});
