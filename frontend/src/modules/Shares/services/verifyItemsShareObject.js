import { gql } from 'apollo-boost';

export const verifyItemsShareObject = ({ input }) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation verifyItemsShareObject($input: ShareItemSelectorInput) {
      verifyItemsShareObject(input: $input) {
        shareUri
        status
      }
    }
  `
});
