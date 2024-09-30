import { gql } from 'apollo-boost';

export const submitShareObject = ({ shareUri }) => ({
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
