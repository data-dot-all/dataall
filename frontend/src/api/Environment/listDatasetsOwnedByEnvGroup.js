import { gql } from 'apollo-boost';

const listDatasetsOwnedByEnvGroup = ({ filter, environmentUri, groupUri }) => ({
  variables: {
    environmentUri,
    groupUri,
    filter
  },
  query: gql`
    query listDatasetsOwnedByEnvGroup(
      $filter: DatasetFilter
      $environmentUri: String
      $groupUri: String
    ) {
      listDatasetsOwnedByEnvGroup(
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

export default listDatasetsOwnedByEnvGroup;
