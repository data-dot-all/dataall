import { gql } from 'apollo-boost';

export const listTableDataFilters = ({ tableUri, filter }) => ({
  variables: {
    tableUri,
    filter
  },
  query: gql`
    query listTableDataFilters(
      $tableUri: String!
      $filter: DatasetTableFilter
    ) {
      listTableDataFilters(tableUri: $tableUri, filter: $filter) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          filterUri
          label
          description
          filterType
          includedCols
          rowExpression
        }
      }
    }
  `
});
