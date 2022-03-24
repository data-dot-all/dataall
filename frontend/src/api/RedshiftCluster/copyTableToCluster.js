import { gql } from 'apollo-boost';

const copyTableToCluster = ({ clusterUri, datasetUri, tableUri, schema, dataLocation }) => ({
  variables: { clusterUri, datasetUri, tableUri, schema, dataLocation },
  mutation: gql`mutation enableRedshiftClusterDatasetTableCopy(
            $clusterUri:String!,
            $datasetUri:String!,
            $tableUri:String!,
            $schema:String!,
            $dataLocation:String
        ){
            enableRedshiftClusterDatasetTableCopy(
                clusterUri:$clusterUri,
                datasetUri:$datasetUri,
                tableUri:$tableUri,
                schema:$schema,
                dataLocation:$dataLocation
            )
        }`
});

export default copyTableToCluster;
