import { gql } from 'apollo-boost';

export const createTerm = ({ input, parentUri }) => ({
  variables: {
    input,
    parentUri
  },
  mutation: gql`
    mutation CreateTerm($parentUri: String!, $input: CreateTermInput) {
      createTerm(parentUri: $parentUri, input: $input) {
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
