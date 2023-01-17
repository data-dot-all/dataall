import { gql } from 'apollo-boost';

const revokeItemsShareObject = ({ shareUri, revokedItemUris }) => ({
  variables: {
    shareUri,
    revokedItemUris
  },
  mutation: gql`
    mutation revokeItemsShareObject($shareUri: String!, $revokedItemUris: [String!]) {
      revokeItemsShareObject(shareUri: $shareUri, revokedItemUris: $revokedItemUris) {
        shareUri
        status
      }
    }
  `
});

export default revokeItemsShareObject;
