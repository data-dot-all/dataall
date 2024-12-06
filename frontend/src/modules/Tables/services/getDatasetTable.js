import { gql } from 'apollo-boost';

export const getDatasetTable = (tableUri) => ({
  variables: {
    tableUri
  },
  query: gql`
    query GetDatasetTable($tableUri: String!) {
      getDatasetTable(tableUri: $tableUri) {
        dataset {
          datasetUri
          name
          userRoleForDataset
          SamlAdminGroupName
          owner
          confidentiality
          environment {
            environmentUri
            label
            region
            organization {
              organizationUri
              label
            }
          }
        }
        datasetUri
        owner
        description
        created
        tags
        tableUri
        LastGlueTableStatus
        label
        name
        restricted {
          S3Prefix
          AwsAccountId
          GlueTableName
          GlueDatabaseName
        }
        terms {
          count
          nodes {
            nodeUri
            path
            label
          }
        }
      }
    }
  `
});
