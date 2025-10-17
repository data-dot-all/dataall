import { gql } from 'apollo-boost';

export const readTableSampleData = ({ tableUri }) => ({
  variables: {
    tableUri
  },
  query: gql`
    query readTableSampleData($tableUri: String!) {
      readTableSampleData(tableUri: $tableUri) {
        fields
        rows
      }
    }
  `
});
