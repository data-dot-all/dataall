import { gql } from 'apollo-boost';

export const listDatasetStorageLocations = (datasetUri, filter) => ({
  variables: {
    datasetUri,
    filter
  },
  query: gql`
    query GetDataset(
      $datasetUri: String!
      $filter: DatasetStorageLocationFilter
    ) {
      getDataset(datasetUri: $datasetUri) {
        datasetUri
        locations(filter: $filter) {
          count
          page
          pages
          hasNext
          hasPrevious
          nodes {
            locationUri
            created
            S3Prefix
            name
            description
            created
            userRoleForStorageLocation
            restricted {
              S3BucketName
            }
          }
        }
      }
    }
  `
});
