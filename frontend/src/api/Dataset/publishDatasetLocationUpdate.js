import { gql } from 'apollo-boost';

const publishDatasetStorageLocationUpdate = ({ locationUri }) => ({
  variables: {
    locationUri
  },
  mutation: gql`
    mutation publishDatasetStorageLocationUpdate($locationUri: String!) {
      publishDatasetStorageLocationUpdate(locationUri: $locationUri)
    }
  `
});

export default publishDatasetStorageLocationUpdate;
