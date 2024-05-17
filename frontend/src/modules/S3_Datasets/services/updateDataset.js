import { gql } from 'apollo-boost';

export const updateDataset = ({ datasetUri, input }) => {
  return {
    variables: {
      datasetUri,
      input
    },
    mutation: gql`
      mutation UpdateDataset($datasetUri: String, $input: ModifyDatasetInput) {
        updateDataset(datasetUri: $datasetUri, input: $input) {
          datasetUri
          label
          tags
          userRoleForDataset
        }
      }
    `
  };
};
