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
          organization {
            label
          }
          environment {
            label
            region
            subscriptionsEnabled
            subscriptionsProducersTopicImported
            subscriptionsConsumersTopicImported
            subscriptionsConsumersTopicName
            subscriptionsProducersTopicName
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
