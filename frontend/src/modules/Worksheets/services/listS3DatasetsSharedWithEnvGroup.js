import { gql } from 'apollo-boost';
export const listS3DatasetsSharedWithEnvGroup = ({
  environmentUri,
  groupUri
}) => ({
  variables: {
    environmentUri,
    groupUri
  },
  query: gql`
    query listS3DatasetsSharedWithEnvGroup(
      $environmentUri: String!
      $groupUri: String!
    ) {
      listS3DatasetsSharedWithEnvGroup(
        environmentUri: $environmentUri
        groupUri: $groupUri
      ) {
        datasetUri
        sharedGlueDatabaseName
        shareUri
      }
    }
  `
});
