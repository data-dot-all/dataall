import { gql } from 'apollo-boost';

export const getDatasetSummary = (datasetUri) => ({
  variables: {
    datasetUri
  },
  query: gql`
    query GetDatasetSummary($datasetUri: String!) {
      getDatasetSummary(datasetUri: $datasetUri)
    }
  `
});
