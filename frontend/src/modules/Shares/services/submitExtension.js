import { gql } from 'apollo-boost';

export const submitExtension = ({
  shareUri,
  expiration,
  extensionReason,
  nonExpirable
}) => ({
  variables: {
    shareUri,
    expiration,
    extensionReason,
    nonExpirable
  },
  mutation: gql`
    mutation submitShareExtension(
      $shareUri: String!
      $expiration: Int
      $extensionReason: String
      $nonExpirable: Boolean
    ) {
      submitShareExtension(
        shareUri: $shareUri
        expiration: $expiration
        extensionReason: $extensionReason
        nonExpirable: $nonExpirable
      ) {
        shareUri
        status
      }
    }
  `
});
