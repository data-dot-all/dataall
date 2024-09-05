import { gql } from 'apollo-boost';

export const approveShareExtension = ({ shareUri }) => ({
  variables: {
    shareUri
  },
  mutation: gql`
    mutation approveShareExtension($shareUri: String!) {
      approveShareExtension(shareUri: $shareUri) {
        shareUri
        status
      }
    }
  `
});
