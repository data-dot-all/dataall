import { gql } from 'apollo-boost';

const previewTable = (tableUri) => ({
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

export default previewTable;
