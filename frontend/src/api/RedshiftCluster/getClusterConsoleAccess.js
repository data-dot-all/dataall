import { gql } from 'apollo-boost';

const getClusterConsoleAccess = (clusterUri) => ({
  variables: {
    clusterUri
  },
  query: gql`
            query getRedshiftClusterConsoleAccess($clusterUri:String!){
                getRedshiftClusterConsoleAccess(clusterUri:$clusterUri)
            }
        `
});

export default getClusterConsoleAccess;
