import { gql } from 'apollo-boost';

export const getDatasetSharedAssumeRoleUrl = (datasetUri) => ({
  variables: {
    datasetUri
  },
  query: gql`
    query GetDatasetSharedAssumeRoleUrl($datasetUri: String!) {
      getDatasetSharedAssumeRoleUrl(datasetUri: $datasetUri)
    }
  `
});
