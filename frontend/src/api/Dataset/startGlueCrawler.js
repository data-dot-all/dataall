import { gql } from 'apollo-boost';

const startGlueCrawler = ({ datasetUri, input }) => ({
  variables: {
    datasetUri,
    input
  },
  mutation: gql`mutation StartGlueCrawler($datasetUri:String, $input:CrawlerInput){
            startGlueCrawler(datasetUri:$datasetUri,input:$input){
                Name
                AwsAccountId
                region
                status
            }
        }`
});

export default startGlueCrawler;
