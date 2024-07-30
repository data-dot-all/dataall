import { gql } from 'apollo-boost';

export const getTablesFolders = (datasetUri) => ({
  variables: {
    datasetUri
  },
  query: gql`
    query GetTablesFolders($datasetUri: String!) {
      getTablesFolders(datasetUri: $datasetUri) {
        name
        type
        targetUri
      }
    }
  `
});
