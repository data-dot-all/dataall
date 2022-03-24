import { gql } from 'apollo-boost';

const getDatasetAssumeRoleUrl = (datasetUri) => ({
  variables: {
    datasetUri
  },
  query: gql`
            query GetDatasetAssumeRoleUrl($datasetUri:String!){
                getDatasetAssumeRoleUrl(datasetUri:$datasetUri)
            }
        `
});

export default getDatasetAssumeRoleUrl;
