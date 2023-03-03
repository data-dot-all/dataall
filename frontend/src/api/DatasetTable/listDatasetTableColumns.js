import { gql } from 'apollo-boost';

const listDatasetTableColumns = ({ tableUri, filter }) => ({
  variables: {
    tableUri,
    filter
  },
  query: gql`
    query ListDatasetTableColumns(
      $tableUri: String!
      $filter: DatasetTableColumnFilter
    ) {
      listDatasetTableColumns(tableUri: $tableUri, filter: $filter) {
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
          lfTagKey
          lfTagValue
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

export default listDatasetTableColumns;
