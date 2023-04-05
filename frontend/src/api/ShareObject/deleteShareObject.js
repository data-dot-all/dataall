import { gql } from 'apollo-boost';

export const deleteShareObject = ({ shareUri }) => ({
  variables: {
    shareUri
  },
  mutation: gql`
    mutation DeleteShareObject($shareUri: String!) {
      deleteShareObject(shareUri: $shareUri)
    }
  `
});
