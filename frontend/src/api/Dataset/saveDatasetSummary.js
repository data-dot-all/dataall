import { gql } from 'apollo-boost';

const saveDatasetSummary = ({ datasetUri, content }) => ({
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

export default saveDatasetSummary;
