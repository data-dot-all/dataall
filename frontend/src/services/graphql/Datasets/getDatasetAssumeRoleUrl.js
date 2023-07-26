import { gql } from 'apollo-boost';

export const getDatasetAssumeRoleUrl = (datasetUri) => ({
  variables: {
    datasetUri
  },
  query: gql`
    query GetDatasetAssumeRoleUrl($datasetUri: String!) {
      getDatasetAssumeRoleUrl(datasetUri: $datasetUri)
    }
  `
});
