import { gql } from 'apollo-boost';

const getAirflowClusterWebLoginToken = (clusterUri) => ({
  variables: {
    clusterUri
  },
  query: gql`
            query getAirflowClusterWebLoginToken($clusterUri:String!){
                getAirflowClusterWebLoginToken(clusterUri:$clusterUri)
            }
        `
});

export default getAirflowClusterWebLoginToken;
