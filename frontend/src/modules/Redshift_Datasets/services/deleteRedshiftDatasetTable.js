import { gql } from 'apollo-boost';

export const deleteRedshiftDatasetTable = ({ datasetUri, rsTableUri }) => ({
  variables: {
    datasetUri,
    rsTableUri
  },
  mutation: gql`
    mutation deleteRedshiftDatasetTable(
      $datasetUri: String!
      $rsTableUri: String!
    ) {
      deleteRedshiftDatasetTable(
        rsTableUri: $rsTableUri
        datasetUri: $datasetUri
      )
    }
  `
});
