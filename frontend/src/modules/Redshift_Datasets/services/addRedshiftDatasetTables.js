import { gql } from 'apollo-boost';

export const addRedshiftDatasetTables = ({ datasetUri, tables }) => ({
  variables: {
    datasetUri,
    tables
  },
  mutation: gql`
    mutation addRedshiftDatasetTables(
      $datasetUri: String!
      $tables: [String]!
    ) {
      addRedshiftDatasetTables(datasetUri: $datasetUri, tables: $tables) {
        successTables
        errorTables
      }
    }
  `
});
