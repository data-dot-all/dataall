import { gql } from 'apollo-boost';

export const archiveDataset = (datasetUri) => ({
  variables: {
    datasetUri
  },
  mutation: gql`
    mutation archiveDataset($datasetUri: String!) {
      archiveDataset(datasetUri: $datasetUri)
    }
  `
});
