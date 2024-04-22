import { gql } from 'apollo-boost';

export const revokeItemsShareObject = ({ input }) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation revokeItemsShareObject($input: ShareItemSelectorInput) {
      revokeItemsShareObject(input: $input) {
        shareUri
        status
      }
    }
  `
});
