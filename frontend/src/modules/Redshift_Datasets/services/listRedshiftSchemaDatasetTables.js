import { gql } from 'apollo-boost';

export const listRedshiftSchemaDatasetTables = ({ datasetUri }) => ({
  variables: {
    datasetUri
  },
  query: gql`
    query listRedshiftSchemaDatasetTables($datasetUri: String!) {
      listRedshiftSchemaTables(datasetUri: $datasetUri) {
        name
        type
        alreadyAdded
      }
    }
  `
});
