import { gql } from 'apollo-boost';

export const getDatasetStorageLocation = (locationUri) => ({
  variables: {
    locationUri
  },
  query: gql`
    query getDatasetStorageLocation($locationUri: String!) {
      getDatasetStorageLocation(locationUri: $locationUri) {
        dataset {
          datasetUri
          name
          userRoleForDataset
          region
          SamlAdminGroupName
          S3BucketName
          AwsAccountId
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
        owner
        description
        created
        tags
        locationUri
        AwsAccountId
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
