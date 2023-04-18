import { gql } from 'apollo-boost';

export const updateDatasetStack = (datasetUri) => ({
  variables: { datasetUri },
  mutation: gql`
    mutation updateDatasetStack($datasetUri: String!) {
      updateDatasetStack(datasetUri: $datasetUri)
    }
  `
});
