import { gql } from 'apollo-boost';

export const textToSQL = ({
  prompt,
  environmentUri,
  worksheetUri,
  datasetUri,
  tableNames
}) => ({
  variables: {
    prompt,
    environmentUri,
    worksheetUri,
    datasetUri,
    tableNames
  },
  query: gql`
    query textToSQL(
      $prompt: String!
      $environmentUri: String!
      $worksheetUri: String!
      $datasetUri: String!
      $tableNames: String
    ) {
      textToSQL(
        prompt: $prompt
        environmentUri: $environmentUri
        worksheetUri: $worksheetUri
        datasetUri: $datasetUri
        tableNames: $tableNames
      )
    }
  `
});
