import { gql } from 'apollo-boost';

export const updateRedshiftDataset = ({ datasetUri, input }) => ({
  variables: {
    datasetUri,
    input
  },
  mutation: gql`
    mutation updateRedshiftDataset(
      $datasetUri: String!
      $input: ModifyRedshiftDatasetInput
    ) {
      updateRedshiftDataset(datasetUri: $datasetUri, input: $input) {
        datasetUri
        label
        userRoleForDataset
      }
    }
  `
});
