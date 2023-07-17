import { gql } from 'apollo-boost';

const submitApproval = ({ shareUri }) => ({
  variables: {
    shareUri
  },
  mutation: gql`
    mutation submitShareObject($shareUri: String!) {
      submitShareObject(shareUri: $shareUri) {
        shareUri
        status
      }
    }
  `
});

export default submitApproval;
