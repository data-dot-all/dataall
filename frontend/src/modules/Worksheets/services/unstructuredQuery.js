import { gql } from 'apollo-boost';

export const unstructuredQuery = ({
  prompt,
  environmentUri,
  worksheetUri,
  datasetS3Bucket,
  key
}) => ({
  variables: {
    prompt,
    environmentUri,
    worksheetUri,
    datasetS3Bucket: datasetS3Bucket,
    key: key
  },
  query: gql`
    query unstructuredQuery(
      $prompt: String!
      $environmentUri: String!
      $worksheetUri: String!
      $datasetS3Bucket: String!
      $key: String
    ) {
      unstructuredQuery(
        prompt: $prompt
        environmentUri: $environmentUri
        worksheetUri: $worksheetUri
        datasetS3Bucket: $datasetS3Bucket
        key: $key
      ) {
        response
      }
    }
  `
});
