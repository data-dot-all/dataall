import { gql } from 'apollo-boost';

export const deleteAttachedMetadataForm = (attachedFormUri) => ({
  variables: {
    attachedFormUri: attachedFormUri
  },
  mutation: gql`
    mutation deleteAttachedMetadataForm($attachedFormUri: String!) {
      deleteAttachedMetadataForm(attachedFormUri: $attachedFormUri)
    }
  `
});
