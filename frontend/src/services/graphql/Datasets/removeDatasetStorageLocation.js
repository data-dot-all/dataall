import { gql } from 'apollo-boost';

export const deleteDatasetStorageLocation = ({ locationUri }) => ({
  variables: { locationUri },
  mutation: gql`
    mutation DeleteDatasetStorageLocation($locationUri: String!) {
      deleteDatasetStorageLocation(locationUri: $locationUri)
    }
  `
});
