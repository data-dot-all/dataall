import { gql } from 'apollo-boost';

export const updateShareExtensionReason = ({ shareUri, extensionPurpose }) => ({
  variables: {
    shareUri: shareUri,
    extensionPurpose: extensionPurpose
  },
  mutation: gql`
    mutation updateShareExtensionReason(
      $shareUri: String!
      $extensionPurpose: String!
    ) {
      updateShareExtensionReason(
        shareUri: $shareUri
        extensionPurpose: $extensionPurpose
      )
    }
  `
});
