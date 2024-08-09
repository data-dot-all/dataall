import { gql } from 'apollo-boost';

export const createMetadataFormFields = (formUri, input) => ({
  variables: {
    formUri: formUri,
    input: input
  },
  mutation: gql`
    mutation createMetadataFormFields(
      $formUri: String!
      $input: [NewMetadataFormFieldInput]
    ) {
      createMetadataFormFields(formUri: $formUri, input: $input) {
        uri
      }
    }
  `
});
