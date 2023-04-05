import { gql } from 'apollo-boost';

export const syncTables = (datasetUri) => ({
  variables: {
    datasetUri
  },
  mutation: gql`
    mutation SyncTables($datasetUri: String!) {
      syncTables(datasetUri: $datasetUri) {
        count
        nodes {
          tableUri
          GlueTableName
          GlueDatabaseName
          description
          name
          label
          created
          S3Prefix
          dataset {
            datasetUri
            name
            GlueDatabaseName
            userRoleForDataset
          }
        }
      }
    }
  `
});
