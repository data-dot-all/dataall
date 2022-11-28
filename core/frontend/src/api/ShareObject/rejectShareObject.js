import { gql } from 'apollo-boost';

const rejectShareObject = ({ shareUri }) => ({
  variables: {
    shareUri
  },
  mutation: gql`
    mutation RejectShareObject($shareUri: String!) {
      rejectShareObject(shareUri: $shareUri) {
        shareUri
        status
      }
    }
  `
});

export default rejectShareObject;
