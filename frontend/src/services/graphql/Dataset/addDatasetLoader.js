import { gql } from 'apollo-boost';

export const createDatasetLoader = ({ datasetUri, input }) => ({
  variables: { input, datasetUri },
  mutation: gql`
    mutation createDatasetLoader(
      $datasetUri: String
      $input: NewDatasetLoaderInput
    ) {
      createDatasetLoader(datasetUri: $datasetUri, input: $input)
    }
  `
});
