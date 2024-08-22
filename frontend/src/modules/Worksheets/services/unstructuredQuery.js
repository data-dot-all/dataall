import { gql } from 'apollo-boost';

export const unstructuredQuery = ({
  prompt,
  environmentUri,
  worksheetUri,
  datasetUri,
  key
}) => ({
  variables: {
    prompt,
    environmentUri,
    worksheetUri,
    datasetUri: datasetUri,
    key: key
  },
  query: gql`
    query unstructuredQuery(
      $prompt: String!
      $environmentUri: String!
      $worksheetUri: String!
      $datasetUri: String!
      $key: String!
    ) {
      unstructuredQuery(
        prompt: $prompt
        environmentUri: $environmentUri
        worksheetUri: $worksheetUri
        datasetUri: $datasetUri
        key: $key
      ) {
        response
      }
    }
  `
});
