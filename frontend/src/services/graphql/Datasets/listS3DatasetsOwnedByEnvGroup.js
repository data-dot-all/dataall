import { gql } from 'apollo-boost';

export const listS3DatasetsOwnedByEnvGroup = ({
  filter,
  environmentUri,
  groupUri
}) => ({
  variables: {
    environmentUri,
    groupUri,
    filter
  },
  query: gql`
    query listS3DatasetsOwnedByEnvGroup(
      $filter: DatasetFilter
      $environmentUri: String!
      $groupUri: String!
    ) {
      listS3DatasetsOwnedByEnvGroup(
        environmentUri: $environmentUri
        groupUri: $groupUri
        filter: $filter
      ) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          datasetUri
          label
          AwsAccountId
          region
          GlueDatabaseName
          SamlAdminGroupName
          name
          S3BucketName
          created
          owner
          stack {
            status
          }
        }
      }
    }
  `
});
