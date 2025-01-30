import { gql } from 'apollo-boost';

export const syncTables = (datasetUri) => ({
  variables: {
    datasetUri
  },
  mutation: gql`
    mutation SyncTables($datasetUri: String!) {
      syncTables(datasetUri: $datasetUri)
    }
  `
});
