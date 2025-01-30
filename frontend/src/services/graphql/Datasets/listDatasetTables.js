import { gql } from 'apollo-boost';

export const listDatasetTables = ({ datasetUri, filter }) => ({
  variables: {
    datasetUri,
    filter
  },
  query: gql`
    query GetDataset($datasetUri: String!, $filter: DatasetTableFilter) {
      getDataset(datasetUri: $datasetUri) {
        tables(filter: $filter) {
          count
          page
          pages
          hasNext
          hasPrevious
          nodes {
            dataset {
              datasetUri
            }
            terms {
              nodes {
                label
              }
            }
            tableUri
            name
            created
            restricted {
              S3Prefix
              AwsAccountId
              GlueTableName
              GlueDatabaseName
            }
            description
            stage
            userRoleForTable
          }
        }
      }
    }
  `
});
