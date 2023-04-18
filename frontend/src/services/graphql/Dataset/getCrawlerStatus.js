import { gql } from 'apollo-boost';

export const getCrawlerStatus = ({ datasetUri, name }) => ({
  variables: {
    datasetUri,
    input: name
  },
  query: gql`query GetCrawlerStatus($datasetUri:String, name:String){
            getCrawlerStatus(datasetUri:$datasetUri,name:$name){
                Name
                AwsAccountId
                region
                status
            }
        }`
});
