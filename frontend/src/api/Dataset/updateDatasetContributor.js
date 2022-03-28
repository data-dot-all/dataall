import { gql } from 'apollo-boost';

const updateDatasetContributor = ({ userName, datasetUri, role }) => ({
  variables: { userName, datasetUri, role },
  mutation: gql`
    mutation UpdateDatasetContributor(
      $datasetUri: String
      $userName: String
      $role: DatasetRole
    ) {
      updateDatasetContributor(
        datasetUri: $datasetUri
        userName: $userName
        role: $role
      ) {
        datasetUri
        label
        userRoleForDataset
      }
    }
  `
});

export default updateDatasetContributor;
