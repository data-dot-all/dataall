import { gql } from 'apollo-boost';

const getDatasetSummary = (datasetUri) => ({
  variables: {
    datasetUri
  },
  query: gql`
    query GetDatasetSummary($datasetUri: String!) {
      getDatasetSummary(datasetUri: $datasetUri)
    }
  `
});

export default getDatasetSummary;
