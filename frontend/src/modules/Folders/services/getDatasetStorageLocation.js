import { gql } from 'apollo-boost';

export const getDatasetStorageLocation = (locationUri) => ({
  variables: {
    locationUri
  },
  query: gql`
    query getDatasetStorageLocation($locationUri: String!) {
      getDatasetStorageLocation(locationUri: $locationUri) {
        restricted {
          AwsAccountId
          region
          S3BucketName
        }
        dataset {
          datasetUri
          name
          label
          userRoleForDataset
          SamlAdminGroupName
          owner
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
