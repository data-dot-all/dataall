import { gql } from 'apollo-boost';

export const listObjectKeys = ({
  datasetUri,
  environmentUri,
  worksheetUri
}) => ({
  variables: {
    datasetUri,
    environmentUri,
    worksheetUri
  },
  query: gql`
    query listObjectKeys(
      $datasetUri: String!
      $environmentUri: String!
      $worksheetUri: String!
    ) {
      listObjectKeys(
        datasetUri: $datasetUri
        environmentUri: $environmentUri
        worksheetUri: $worksheetUri
      ) {
        objectKeys
      }
    }
  `
});
