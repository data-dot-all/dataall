import { gql } from 'apollo-boost';

export const getRedshiftDatasetTableColumns = ({
  datasetUri,
  rsTableUri,
  filter
}) => ({
  variables: {
    datasetUri,
    rsTableUri,
    filter
  },
  query: gql`
    query getRedshiftDatasetTableColumns(
      $datasetUri: String!
      $rsTableUri: String!
      $filter: RedshiftDatasetTableFilter
    ) {
      getRedshiftDatasetTableColumns(
        datasetUri: $datasetUri
        rsTableUri: $rsTableUri
        filter: $filter
      ) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          columnDefault
          label
          length
          name
          nullable
          typeName
        }
      }
    }
  `
});
