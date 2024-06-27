import { gql } from 'apollo-boost';

export const reApplyShareObjectItemsOnDataset = ({ datasetUri }) => ({
  variables: {
    datasetUri
  },
  mutation: gql`
    mutation reApplyShareObjectItemsOnDataset($datasetUri: String!) {
      reApplyShareObjectItemsOnDataset(datasetUri: $datasetUri)
    }
  `
});
