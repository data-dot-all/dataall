import { gql } from 'apollo-boost';

export const submitExtension = ({ shareUri, expiration, extensionReason }) => ({
  variables: {
    shareUri,
    expiration,
    extensionReason
  },
  mutation: gql`
    mutation submitShareExtension(
      $shareUri: String!
      $expiration: Int!
      $extensionReason: String
    ) {
      submitShareExtension(
        shareUri: $shareUri
        expiration: $expiration
        extensionReason: $extensionReason
      ) {
        shareUri
        status
      }
    }
  `
});
