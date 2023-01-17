import { gql } from 'apollo-boost';

const revokeItemsShareObject = ({ input }) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation revokeItemsShareObject($input: RevokeItemsInput) {
      revokeItemsShareObject(input: $input) {
        shareUri
        status
      }
    }
  `
});

export default revokeItemsShareObject;
