import { gql } from 'apollo-boost';

export const createMetadataForm = (input) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation createMetadataForm($input: NewMetadataFormInput!) {
      createMetadataForm(input: $input) {
        uri
      }
    }
  `
});
