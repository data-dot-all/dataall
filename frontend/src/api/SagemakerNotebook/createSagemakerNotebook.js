import { gql } from 'apollo-boost';

export const createSagemakerNotebook = (input) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation CreateSagemakerNotebook($input: NewSagemakerNotebookInput) {
      createSagemakerNotebook(input: $input) {
        notebookUri
        name
        label
        created
        description
        tags
      }
    }
  `
});
