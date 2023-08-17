import { gql } from 'apollo-boost';

export const startSagemakerNotebook = (notebookUri) => ({
  variables: {
    notebookUri
  },
  mutation: gql`
    mutation StartSagemakerNotebook($notebookUri: String!) {
      startSagemakerNotebook(notebookUri: $notebookUri)
    }
  `
});
