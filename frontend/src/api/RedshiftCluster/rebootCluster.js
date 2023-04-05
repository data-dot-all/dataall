import { gql } from 'apollo-boost';

export const rebootRedshiftCluster = (clusterUri) => ({
  variables: {
    clusterUri
  },
  mutation: gql`
    mutation rebootRedshiftCluster($clusterUri: String!) {
      rebootRedshiftCluster(clusterUri: $clusterUri)
    }
  `
});
