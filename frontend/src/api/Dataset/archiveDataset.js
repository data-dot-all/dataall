import { gql } from 'apollo-boost';

const archiveDataset = (datasetUri) => ({
  variables: {
    datasetUri
  },
  mutation: gql`
    mutation archiveDataset($datasetUri: String!) {
      archiveDataset(datasetUri: $datasetUri)
    }
  `
});

export default archiveDataset;
