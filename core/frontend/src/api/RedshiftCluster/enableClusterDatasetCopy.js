import { gql } from 'apollo-boost';

const enableRedshiftClusterDatasetCopy = ({ clusterUri, datasetUri }) => ({
  variables: { clusterUri, datasetUri },
  mutation: gql`
    mutation enableRedshiftClusterDatasetCopy(
      $clusterUri: String
      $datasetUri: String
    ) {
      enableRedshiftClusterDatasetCopy(
        clusterUri: $clusterUri
        datasetUri: $datasetUri
      )
    }
  `
});

export default enableRedshiftClusterDatasetCopy;
