import { gql } from 'apollo-boost';

export const createMetadataFormVersion = (formUri, copyVersion) => ({
  variables: {
    formUri: formUri,
    copyVersion: copyVersion
  },
  mutation: gql`
    mutation createMetadataFormVersion($formUri: String!, $copyVersion: Int) {
      createMetadataFormVersion(formUri: $formUri, copyVersion: $copyVersion)
    }
  `
});
