import { gql } from 'apollo-boost';

const getDatasetPresignedUrl = ({ datasetUri, input }) => ({
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

export default getDatasetPresignedUrl;
