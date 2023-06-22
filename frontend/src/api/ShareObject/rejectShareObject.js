import { gql } from 'apollo-boost';

const rejectShareObject = ({ shareUri, rejectPurpose }) => ({
  variables: {
    shareUri,
    rejectPurpose
  },
  mutation: gql`
    mutation RejectShareObject($shareUri: String!, $rejectPurpose: String!) {
      rejectShareObject(shareUri: $shareUri,rejectPurpose: $rejectPurpose) {
        shareUri
        status
      }
    }
  `
});

export default rejectShareObject;
