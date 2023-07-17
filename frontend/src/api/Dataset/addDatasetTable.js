import { gql } from 'apollo-boost';

const createDatasetTable = ({ datasetUri, input }) => ({
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

export default createDatasetTable;
