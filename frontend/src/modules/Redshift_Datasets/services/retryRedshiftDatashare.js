import { gql } from 'apollo-boost';

export const retryRedshiftDatashare = (datasetUri) => ({
  variables: {
    datasetUri
  },
  mutation: gql`
    mutation retryRedshiftDatashare($datasetUri: String!) {
      retryRedshiftDatashare(datasetUri: $datasetUri) {
        dataShareStatus
      }
    }
  `
});
