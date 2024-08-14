import { gql } from 'apollo-boost';

export const getDatasetExpirationDetails = ({ datasetUri }) => ({
  variables: {
    datasetUri
  },
  query: gql`
    query GetDataset($datasetUri: String!) {
      getDataset(datasetUri: $datasetUri) {
        datasetUri
        label
        description
        enableExpiration
        expirySetting
        expiryMinDuration
        expiryMaxDuration
      }
    }
  `
});
