import { gql } from 'apollo-boost';

const getStackLogs = (environmentUri, stackUri) => ({
  variables: {
    environmentUri,
    stackUri
  },
  query: gql`
            query getStackLogs($environmentUri:String!,$stackUri:String!){
                getStackLogs(environmentUri:$environmentUri,stackUri:$stackUri){
                    message
                    timestamp
                }
            }
        `
});

export default getStackLogs;
