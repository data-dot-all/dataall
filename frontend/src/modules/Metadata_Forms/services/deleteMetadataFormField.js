import { gql } from 'apollo-boost';

export const deleteMetadataFormField = (formUri, fieldUri) => ({
  variables: {
    formUri: formUri,
    fieldUri: fieldUri
  },
  mutation: gql`
    mutation deleteMetadataFormField($formUri: String!, $fieldUri: String!) {
      deleteMetadataFormField(formUri: $formUri, fieldUri: $fieldUri)
    }
  `
});
