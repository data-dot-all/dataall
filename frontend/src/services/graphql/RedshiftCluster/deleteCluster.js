import { gql } from 'apollo-boost';

export const deleteRedshiftCluster = (clusterUri, deleteFromAWS) => ({
  variables: {
    clusterUri,
    deleteFromAWS
  },
  mutation: gql`
    mutation deleteRedshiftCluster(
      $clusterUri: String!
      $deleteFromAWS: Boolean
    ) {
      deleteRedshiftCluster(
        clusterUri: $clusterUri
        deleteFromAWS: $deleteFromAWS
      )
    }
  `
});
