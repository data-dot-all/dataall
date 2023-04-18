import { gql } from 'apollo-boost';

export const getRedshiftClusterConsoleAccess = (clusterUri) => ({
  variables: {
    clusterUri
  },
  query: gql`
    query getRedshiftClusterConsoleAccess($clusterUri: String!) {
      getRedshiftClusterConsoleAccess(clusterUri: $clusterUri)
    }
  `
});
