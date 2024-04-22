import { gql } from 'apollo-boost';

export const reApplyItemsShareObject = ({ input }) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation reApplyItemsShareObject($input: ShareItemSelectorInput) {
      reApplyItemsShareObject(input: $input) {
        shareUri
        status
      }
    }
  `
});
