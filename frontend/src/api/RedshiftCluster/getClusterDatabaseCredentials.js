import { gql } from 'apollo-boost';

export const getRedshiftClusterDatabaseCredentials = (clusterUri) => ({
  variables: {
    clusterUri
  },
  query: gql`
    query getRedshiftClusterDatabaseCredentials($clusterUri: String!) {
      getRedshiftClusterDatabaseCredentials(clusterUri: $clusterUri) {
        clusterUri
        user
        database
        port
        endpoint
        password
      }
    }
  `
});
