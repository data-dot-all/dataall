import { gql } from 'apollo-boost';

export const cancelShareExtensionObject = ({ shareUri }) => ({
  variables: {
    shareUri
  },
  mutation: gql`
    mutation cancelShareExtensionObject($shareUri: String!) {
      cancelShareExtensionObject(shareUri: $shareUri)
    }
  `
});
