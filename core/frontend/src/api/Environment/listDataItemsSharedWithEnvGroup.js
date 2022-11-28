import { gql } from 'apollo-boost';

const listDataItemsSharedWithEnvGroup = ({ filter, environmentUri, groupUri }) => ({
  variables: {
    environmentUri,
    groupUri,
    filter
  },
  query: gql`
    query listDataItemsSharedWithEnvGroup(
      $filter: EnvironmentDataItemFilter
      $environmentUri: String
      $groupUri: String
    ) {
      listDataItemsSharedWithEnvGroup(
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
          shareUri
          environmentName
          environmentUri
          organizationName
          organizationUri
          datasetUri
          datasetName
          itemType
          itemAccess
          GlueDatabaseName
          GlueTableName
          S3AccessPointName
          created
          principalId
        }
      }
    }
  `
});

export default listDataItemsSharedWithEnvGroup;
