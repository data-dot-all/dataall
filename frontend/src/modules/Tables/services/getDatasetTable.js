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
          region
          SamlAdminGroupName
          owner
          confidentiality
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
        AwsAccountId
        GlueTableName
        GlueDatabaseName
        LastGlueTableStatus
        label
        name
        S3Prefix
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
