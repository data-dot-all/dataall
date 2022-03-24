import { gql } from 'apollo-boost';

const pauseRedshiftCluster = (clusterUri) => ({
  variables: {
    clusterUri
  },
  mutation: gql`mutation pauseRedshiftCluster(
            $clusterUri : String!
        ){
            pauseRedshiftCluster(clusterUri:$clusterUri)
        }`
});

export default pauseRedshiftCluster;
