import { gql } from 'apollo-boost';

const listDatasetStorageLocations = (datasetUri, filter) => ({
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
          nodes {
            locationUri
            created
            S3Prefix
            name
            description
            created
            userRoleForStorageLocation
          }
        }
      }
    }
  `
});

export default listDatasetStorageLocations;
