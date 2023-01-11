import { gql } from 'apollo-boost';

const syncDatasetTableColumns = (tableUri) => ({
  variables: {
    tableUri
  },
  mutation: gql`
    mutation SyncDatasetTableColumns($tableUri: String!) {
      syncDatasetTableColumns(tableUri: $tableUri) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          columnUri
          name
          description
          typeName
          lfTagKey
          lfTagValue
        }
      }
    }
  `
});

export default syncDatasetTableColumns;
