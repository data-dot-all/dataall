import { gql } from 'apollo-boost';

export const previewTable = (tableUri) => ({
  variables: {
    tableUri
  },
  query: gql`
    query PreviewTable($tableUri: String!) {
      previewTable(tableUri: $tableUri) {
        rows
        fields
      }
    }
  `
});
