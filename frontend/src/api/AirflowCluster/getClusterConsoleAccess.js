import { gql } from 'apollo-boost';

const getClusterConsoleAccess = (clusterUri) => ({
  variables: {
    clusterUri
  },
  query: gql`
            query getAirflowClusterConsoleAccess($clusterUri:String!){
                getAirflowClusterConsoleAccess(clusterUri:$clusterUri)
            }
        `
});

export default getClusterConsoleAccess;
