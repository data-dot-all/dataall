import { gql } from 'apollo-boost';

const deleteShareObject = ({ shareUri }) => ({
  variables: {
    shareUri
  },
  mutation: gql`
    mutation DeleteShareObject($shareUri: String!) {
      deleteShareObject(shareUri: $shareUri)
    }
  `
});

export default deleteShareObject;
