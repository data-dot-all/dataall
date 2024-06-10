import { gql } from 'apollo-boost';

export const generateDatasetAccessToken = (datasetUri) => ({
  variables: {
    datasetUri
  },
  mutation: gql`
    mutation GenerateDatasetAccessToken($datasetUri: String!) {
      generateDatasetAccessToken(datasetUri: $datasetUri)
    }
  `
});
