import { gql } from 'apollo-boost';

export const listClusterDatasetTables = ({ clusterUri, filter }) => ({
  variables: {
    clusterUri,
    filter
  },
  query: gql`
    query listRedshiftClusterCopyEnabledTables(
      $clusterUri: String!
      $filter: DatasetTableFilter
    ) {
      listRedshiftClusterCopyEnabledTables(
        clusterUri: $clusterUri
        filter: $filter
      ) {
        count
        page
        pages
        hasNext
        hasPrevious
        count
        nodes {
          datasetUri
          tableUri
          name
          label
          GlueDatabaseName
          GlueTableName
          S3Prefix
          AwsAccountId
          RedshiftSchema(clusterUri: $clusterUri)
          RedshiftCopyDataLocation(clusterUri: $clusterUri)
        }
      }
    }
  `
});
