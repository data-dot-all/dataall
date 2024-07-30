import { gql } from 'apollo-boost';

export const getRedshiftDatasetTableColumns = ({ rsTableUri, filter }) => ({
  variables: {
    rsTableUri,
    filter
  },
  query: gql`
    query getRedshiftDatasetTableColumns(
      $rsTableUri: String!
      $filter: RedshiftDatasetTableFilter
    ) {
      getRedshiftDatasetTableColumns(rsTableUri: $rsTableUri, filter: $filter) {
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
