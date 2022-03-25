import { gql } from 'apollo-boost';

const listAvailableDatasetTables = ({ clusterUri, filter }) => ({
  variables: {
    clusterUri,
    filter
  },
  query: gql`
    query listRedshiftClusterAvailableDatasetTables(
      $clusterUri: String!
      $filter: DatasetTableFilter
    ) {
      listRedshiftClusterAvailableDatasetTables(
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
          dataset {
            S3BucketName
          }
        }
      }
    }
  `
});

export default listAvailableDatasetTables;
