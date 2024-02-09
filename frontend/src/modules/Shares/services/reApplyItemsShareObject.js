import { gql } from 'apollo-boost';

export const reApplyItemsShareObject = ({ input }) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation reApplyItemsShareObject($input: RevokeItemsInput) {
      reApplyItemsShareObject(input: $input) {
        shareUri
        status
      }
    }
  `
});
