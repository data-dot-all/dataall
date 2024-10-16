import { gql } from 'apollo-boost';

export const listObjectKeys = ({ datasetUri }) => ({
  variables: {
    datasetUri
  },
  query: gql`
    query listObjectKeys($datasetUri: String!) {
      listObjectKeys(datasetUri: $datasetUri) {
        objectKeys
      }
    }
  `
});
