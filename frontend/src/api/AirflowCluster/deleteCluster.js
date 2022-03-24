import { gql } from 'apollo-boost';

const deleteAirflowCluster = (clusterUri) => ({
  variables: {
    clusterUri
  },
  mutation: gql`mutation deleteAirflowCluster(
            $clusterUri : String!
        ){
            deleteAirflowCluster(clusterUri:$clusterUri)
        }`
});

export default deleteAirflowCluster;
