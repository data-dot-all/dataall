import { gql } from 'apollo-boost';

export const getDatasetETLCredentials = (datasetUri) => ({
  variables: {
    datasetUri
  },
  query: gql`
    query GetDatasetETLCredentials($datasetUri: String!) {
      getDatasetETLCredentials(datasetUri: $datasetUri)
    }
  `
});
