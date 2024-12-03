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
          SamlAdminGroupName
          owner
          restricted {
            AwsAccountId
            region
            S3BucketName
          }
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
        owner
        description
        created
        tags
        locationUri
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
