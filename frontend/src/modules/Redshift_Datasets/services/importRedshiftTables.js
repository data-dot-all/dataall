import { gql } from 'apollo-boost';

export const importRedshiftTables = (input) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation importRedshiftTables($input: ImportRedshiftTablesInput) {
      importRedshiftTables(input: $input) {
        datasetUri
        label
        userRoleForDataset
      }
    }
  `
});
