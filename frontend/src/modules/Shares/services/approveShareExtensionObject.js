import { gql } from 'apollo-boost';

export const approveShareExtensionObject = ({ shareUri }) => ({
  variables: {
    shareUri
  },
  mutation: gql`
    mutation approveShareExtensionObject($shareUri: String!) {
      approveShareExtensionObject(shareUri: $shareUri) {
        shareUri
        status
      }
    }
  `
});
