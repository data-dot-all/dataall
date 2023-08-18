import { gql } from 'apollo-boost';

export const updateDatasetStorageLocation = ({ locationUri, input }) => ({
  variables: {
    locationUri,
    input
  },
  mutation: gql`
    mutation updateDatasetStorageLocation(
      $locationUri: String!
      $input: ModifyDatasetStorageLocationInput!
    ) {
      updateDatasetStorageLocation(locationUri: $locationUri, input: $input) {
        locationUri
      }
    }
  `
});
