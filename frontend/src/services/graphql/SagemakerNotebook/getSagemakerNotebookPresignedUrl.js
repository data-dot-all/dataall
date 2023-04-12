import { gql } from 'apollo-boost';

export const getSagemakerNotebookPresignedUrl = (notebookUri) => ({
  variables: {
    notebookUri
  },
  query: gql`
    query getSagemakerNotebookPresignedUrl($notebookUri: String!) {
      getSagemakerNotebookPresignedUrl(notebookUri: $notebookUri)
    }
  `
});
