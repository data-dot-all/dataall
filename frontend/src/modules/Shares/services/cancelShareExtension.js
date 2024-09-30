import { gql } from 'apollo-boost';

export const cancelShareExtension = ({ shareUri }) => ({
  variables: {
    shareUri
  },
  mutation: gql`
    mutation cancelShareExtension($shareUri: String!) {
      cancelShareExtension(shareUri: $shareUri)
    }
  `
});
