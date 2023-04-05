import { gql } from 'apollo-boost';

export const importDataset = (input) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation ImportDataset($input: ImportDatasetInput) {
      importDataset(input: $input) {
        datasetUri
        label
        userRoleForDataset
      }
    }
  `
});
