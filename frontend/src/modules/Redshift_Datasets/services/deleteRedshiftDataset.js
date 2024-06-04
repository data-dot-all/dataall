import { gql } from 'apollo-boost';

export const deleteRedshiftDataset = (datasetUri, deleteFromAWS) => ({
  variables: {
    datasetUri,
    deleteFromAWS
  },
  mutation: gql`
    mutation deleteRedshiftDataset(
      $datasetUri: String!
      $deleteFromAWS: Boolean
    ) {
      deleteRedshiftDataset(
        datasetUri: $datasetUri
        deleteFromAWS: $deleteFromAWS
      )
    }
  `
});
