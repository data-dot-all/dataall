import { gql } from 'apollo-boost';

const getSharedDatasetTables = ({ datasetUri, envUri }) => ({
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

export default getSharedDatasetTables;
