import { gql } from 'apollo-boost';

export const batchMetadataFormFieldUpdates = (formUri, input) => ({
  variables: {
    formUri: formUri,
    input: input
  },
  mutation: gql`
    mutation batchMetadataFormFieldUpdates(
      $formUri: String!
      $input: [MetadataFormFieldUpdateInput]
    ) {
      batchMetadataFormFieldUpdates(formUri: $formUri, input: $input) {
        uri
        metadataFormUri
        name
        required
        type
        glossaryNodeUri
        possibleValues
      }
    }
  `
});
