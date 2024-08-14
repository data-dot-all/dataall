import { gql } from 'apollo-boost';

export const updateShareExpirationPeriod = ({ shareUri, expiration }) => ({
  variables: {
    shareUri,
    expiration
  },
  mutation: gql`
    mutation updateShareExpirationPeriod($shareUri: String!, $expiration: Int) {
      updateShareExpirationPeriod(shareUri: $shareUri, expiration: $expiration)
    }
  `
});
