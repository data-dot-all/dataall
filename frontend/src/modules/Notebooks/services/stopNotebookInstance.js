import { gql } from 'apollo-boost';

export const stopSagemakerNotebook = (notebookUri) => ({
  variables: {
    notebookUri
  },
  mutation: gql`
    mutation StopSagemakerNotebook($notebookUri: String!) {
      stopSagemakerNotebook(notebookUri: $notebookUri)
    }
  `
});
