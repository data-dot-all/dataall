import { gql } from 'apollo-boost';

export const removeDatasetFromCluster = ({ clusterUri, datasetUri }) => ({
  variables: { clusterUri, datasetUri },
  mutation: gql`
    mutation removeDatasetFromRedshiftCluster(
      $clusterUri: String
      $datasetUri: String
    ) {
      removeDatasetFromRedshiftCluster(
        clusterUri: $clusterUri
        datasetUri: $datasetUri
      )
    }
  `
});
