import { gql } from 'apollo-boost';

export const importRedshiftDataset = (input) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation importRedshiftDataset($input: ImportRedshiftDatasetInput) {
      importRedshiftDataset(input: $input) {
        datasetUri
        label
        userRoleForDataset
        addedTables {
          errorTables
          successTables
        }
      }
    }
  `
});
