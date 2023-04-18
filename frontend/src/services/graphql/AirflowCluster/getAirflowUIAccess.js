import { gql } from 'apollo-boost';

export const getAirflowClusterWebLoginToken = (clusterUri) => ({
  variables: {
    clusterUri
  },
  query: gql`
    query getAirflowClusterWebLoginToken($clusterUri: String!) {
      getAirflowClusterWebLoginToken(clusterUri: $clusterUri)
    }
  `
});
