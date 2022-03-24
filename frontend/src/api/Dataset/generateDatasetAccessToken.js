import { gql } from 'apollo-boost';

const generateDatasetAccessToken = (datasetUri) => ({
  variables: {
    datasetUri
  },
  mutation: gql`
            mutation GenerateDatasetAccessToken($datasetUri:String!){
                generateDatasetAccessToken(datasetUri:$datasetUri)
            }
        `
});

export default generateDatasetAccessToken;
