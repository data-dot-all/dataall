import { gql } from 'apollo-boost';

export const deleteAttachedMetadataForm = (attachedFormUri) => ({
  variables: {
    formUri: attachedFormUri
  },
  mutation: gql`
    mutation deleteAttachedMetadataForm($formUri: String!) {
      deleteAttachedMetadataForm(formUri: $formUri)
    }
  `
});
