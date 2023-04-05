import { gql } from 'apollo-boost';

export const approveShareObject = ({ shareUri }) => ({
  variables: {
    shareUri
  },
  mutation: gql`
    mutation approveShareObject($shareUri: String!) {
      approveShareObject(shareUri: $shareUri) {
        shareUri
        status
      }
    }
  `
});
