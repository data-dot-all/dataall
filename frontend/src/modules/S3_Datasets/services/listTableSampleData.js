import { gql } from 'apollo-boost';

export const listTableSampleData = ({ tableUri }) => ({
  variables: {
    tableUri
  },
  query: gql`
    query listTableSampleData($tableUri: String!) {
      listTableSampleData(tableUri: $tableUri) {
        fields
        rows
      }
    }
  `
});
