import { gql } from 'apollo-boost';

const createOmicsRun = (input) => ({
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

export default createOmicsRun;
