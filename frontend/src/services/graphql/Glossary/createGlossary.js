import { gql } from 'apollo-boost';

export const createGlossary = (input) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation CreateGlossary($input: CreateGlossaryInput) {
      createGlossary(input: $input) {
        nodeUri
        label
        path
        readme
        created
        owner
      }
    }
  `
});
