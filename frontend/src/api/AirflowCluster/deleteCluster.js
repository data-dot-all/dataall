import { gql } from 'apollo-boost';

export const deleteAirflowCluster = (clusterUri) => ({
  variables: {
    clusterUri
  },
  mutation: gql`
    mutation deleteAirflowCluster($clusterUri: String!) {
      deleteAirflowCluster(clusterUri: $clusterUri)
    }
  `
});
