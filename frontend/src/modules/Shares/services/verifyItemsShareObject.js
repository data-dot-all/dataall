import { gql } from 'apollo-boost';

export const verifyItemsShareObject = ({ input }) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation verifyItemsShareObject($input: RevokeItemsInput) {
      verifyItemsShareObject(input: $input) {
        shareUri
        status
      }
    }
  `
});
