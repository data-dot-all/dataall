import { gql } from 'apollo-boost';

export const createOmicsRun = (input) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation createOmicsRun($input: NewOmicsRunInput) {
      createOmicsRun(input: $input) {
        sagemakerStudioUserUri
        name
        label
        created
        description
        tags
      }
    }
  `
});
