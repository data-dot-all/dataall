import { gql } from 'apollo-boost';

export const saveDatasetSummary = ({ datasetUri, content }) => ({
  variables: {
    datasetUri,
    content
  },
  mutation: gql`
    mutation SaveDatasetSummary($datasetUri: String!, $content: String) {
      saveDatasetSummary(datasetUri: $datasetUri, content: $content)
    }
  `
});
