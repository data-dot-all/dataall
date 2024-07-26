import { gql } from 'apollo-boost';

export const createMetadataForm = (input) => ({
  variables: {
    input
  },
  query: gql`
    query createMetadataForm($input: NewMetadataFormInput) {
      createMetadataForm(input: $input) {
        uri
      }
    }
  `
});
