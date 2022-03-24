import { gql } from 'apollo-boost';

const addDatasetToCluster = ({ clusterUri, datasetUri }) => ({
  variables: { clusterUri, datasetUri },
  mutation: gql`mutation addDatasetToRedshiftCluster(
            $clusterUri:String,
            $datasetUri:String,
        ){
            addDatasetToRedshiftCluster(
                clusterUri:$clusterUri,
                datasetUri:$datasetUri
            )
        }`
});

export default addDatasetToCluster;
