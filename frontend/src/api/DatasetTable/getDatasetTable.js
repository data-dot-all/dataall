import { gql } from 'apollo-boost';

const getDatasetTable = (tableUri) => ({
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
        GlueTableProperties
        lfTagKey
        lfTagValue
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

export default getDatasetTable;
