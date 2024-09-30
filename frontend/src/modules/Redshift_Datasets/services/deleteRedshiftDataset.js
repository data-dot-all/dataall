import { gql } from 'apollo-boost';

export const deleteRedshiftDataset = (datasetUri) => ({
  variables: {
    datasetUri
  },
  mutation: gql`
    mutation deleteRedshiftDataset($datasetUri: String!) {
      deleteRedshiftDataset(datasetUri: $datasetUri)
    }
  `
});
