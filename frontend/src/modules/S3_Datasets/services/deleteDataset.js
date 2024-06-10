import { gql } from 'apollo-boost';

export const deleteDataset = (datasetUri, deleteFromAWS) => ({
  variables: {
    datasetUri,
    deleteFromAWS
  },
  mutation: gql`
    mutation deleteDataset($datasetUri: String!, $deleteFromAWS: Boolean) {
      deleteDataset(datasetUri: $datasetUri, deleteFromAWS: $deleteFromAWS)
    }
  `
});
