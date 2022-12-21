import { gql } from 'apollo-boost';

const revokeAllShareObject = ({ shareUri }) => ({
  variables: {
    shareUri
  },
  mutation: gql`
    mutation revokeAllShareObject($shareUri: String!) {
      revokeAllShareObject(shareUri: $shareUri) {
        shareUri
        status
      }
    }
  `
});

export default revokeAllShareObject;
