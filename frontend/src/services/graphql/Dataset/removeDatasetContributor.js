import { gql } from 'apollo-boost';

export const removeDatasetContributor = ({ userName, datasetUri }) => ({
  variables: { userName, datasetUri },
  mutation: gql`
    mutation RemoveDatasetContributor($datasetUri: String, $userName: String) {
      removeDatasetContributor(datasetUri: $datasetUri, userName: $userName) {
        datasetUri
        label
        userRoleForDataset
      }
    }
  `
});
