import { gql } from 'apollo-boost';

export const resumeRedshiftCluster = (clusterUri) => ({
  variables: {
    clusterUri
  },
  mutation: gql`
    mutation resumeRedshiftCluster($clusterUri: String!) {
      resumeRedshiftCluster(clusterUri: $clusterUri)
    }
  `
});
