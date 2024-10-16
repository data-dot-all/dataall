import { gql } from 'apollo-boost';

export const textToSQL = ({
  prompt,
  environmentUri,
  groupUri,
  datasetUri,
  tableNames
}) => ({
  variables: {
    prompt,
    environmentUri,
    groupUri,
    datasetUri,
    tableNames
  },
  query: gql`
    query textToSQL(
      $prompt: String!
      $environmentUri: String!
      $groupUri: String!
      $datasetUri: String!
      $tableNames: String
    ) {
      textToSQL(
        prompt: $prompt
        environmentUri: $environmentUri
        groupUri: $groupUri
        datasetUri: $datasetUri
        tableNames: $tableNames
      )
    }
  `
});
