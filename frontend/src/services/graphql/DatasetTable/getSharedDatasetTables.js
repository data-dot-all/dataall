import { gql } from 'apollo-boost';

export const getSharedDatasetTables = ({ datasetUri, envUri }) => ({
  variables: {
    datasetUri,
    envUri
  },
  query: gql`
    query GetSharedDatasetTables($datasetUri: String!, $envUri: String!) {
      getSharedDatasetTables(datasetUri: $datasetUri, envUri: $envUri) {
        tableUri
        GlueTableName
      }
    }
  `
});
