import { gql } from 'apollo-boost';

export const deleteMetadataForm = (formUri) => ({
  variables: {
    formUri: formUri
  },
  mutation: gql`
    mutation deleteMetadataForm($formUri: String!) {
      deleteMetadataForm(formUri: $formUri)
    }
  `
});
