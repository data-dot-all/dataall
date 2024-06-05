import { gql } from 'apollo-boost';

export const retryRedshiftDatashare = (datasetUri) => ({
  variables: {
    datasetUri
  },
  query: gql`
    query retryRedshiftDatashare($datasetUri: String!) {
      retryRedshiftDatashare(datasetUri: $datasetUri) {
        datasetUri
        owner
      }
    }
  `
});
