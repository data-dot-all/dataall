import { gql } from 'apollo-boost';

export const createDatasetTable = ({ datasetUri, input }) => ({
  variables: { datasetUri, input },
  mutation: gql`
    mutation CreateDatasetTable(
      $datasetUri: String
      $input: NewDatasetTableInput
    ) {
      createDatasetTable(datasetUri: $datasetUri, input: $input) {
        tableUri
        name
      }
    }
  `
});
