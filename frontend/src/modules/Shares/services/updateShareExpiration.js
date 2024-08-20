import { gql } from 'apollo-boost';

export const updateShareExpirationPeriod = ({
  shareUri,
  expiration,
  nonExpirable
}) => ({
  variables: {
    shareUri,
    expiration,
    nonExpirable
  },
  mutation: gql`
    mutation updateShareExpirationPeriod(
      $shareUri: String!
      $expiration: Int
      $nonExpirable: Boolean
    ) {
      updateShareExpirationPeriod(
        shareUri: $shareUri
        expiration: $expiration
        nonExpirable: $nonExpirable
      )
    }
  `
});
