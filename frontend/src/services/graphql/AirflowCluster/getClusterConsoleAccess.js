import { gql } from 'apollo-boost';

export const getAirflowClusterConsoleAccess = (clusterUri) => ({
  variables: {
    clusterUri
  },
  query: gql`
    query getAirflowClusterConsoleAccess($clusterUri: String!) {
      getAirflowClusterConsoleAccess(clusterUri: $clusterUri)
    }
  `
});
