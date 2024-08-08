import { gql } from 'apollo-boost';

export const listSharedDatasetTableColumns = ({
  tableUri,
  shareUri,
  filter
}) => ({
  variables: {
    tableUri,
    shareUri,
    filter
  },
  query: gql`
    query listSharedDatasetTableColumns(
      $tableUri: String!
      $shareUri: String!
      $filter: DatasetTableColumnFilter
    ) {
      listSharedDatasetTableColumns(
        tableUri: $tableUri
        shareUri: $shareUri
        filter: $filter
      ) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          columnUri
          name
          label
          description
          typeName
          columnType
          terms {
            count
            page
            pages
            nodes {
              linkUri
              term {
                label
                created
                path
                nodeUri
              }
            }
          }
        }
      }
    }
  `
});
