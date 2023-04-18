import { gql } from 'apollo-boost';

export const pauseRedshiftCluster = (clusterUri) => ({
  variables: {
    clusterUri
  },
  mutation: gql`
    mutation pauseRedshiftCluster($clusterUri: String!) {
      pauseRedshiftCluster(clusterUri: $clusterUri)
    }
  `
});
