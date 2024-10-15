import { gql } from 'apollo-boost';

export const deleteMetadataFormVersion = (formUri, version) => ({
  variables: {
    formUri: formUri,
    version: version
  },
  mutation: gql`
    mutation deleteMetadataFormVersion($formUri: String!, $version: Int) {
      deleteMetadataFormVersion(formUri: $formUri, version: $version)
    }
  `
});
