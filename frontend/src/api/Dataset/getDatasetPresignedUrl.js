import { gql } from 'apollo-boost';

export const getDatasetPresignedUrl = ({ datasetUri, input }) => ({
  variables: {
    datasetUri,
    input
  },
  query: gql`
    query GetDatasetPresignedUrl(
      $datasetUri: String!
      $input: DatasetPresignedUrlInput
    ) {
      getDatasetPresignedUrl(datasetUri: $datasetUri, input: $input)
    }
  `
});
