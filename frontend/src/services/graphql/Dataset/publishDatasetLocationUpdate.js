import { gql } from 'apollo-boost';

export const publishDatasetStorageLocationUpdate = ({ locationUri }) => ({
  variables: {
    locationUri
  },
  mutation: gql`
    mutation publishDatasetStorageLocationUpdate($locationUri: String!) {
      publishDatasetStorageLocationUpdate(locationUri: $locationUri)
    }
  `
});
