import { gql } from 'apollo-boost';

const createSagemakerStudioUser = (input) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation createSagemakerStudioUser(
      $input: NewSagemakerStudioUserInput
    ) {
      createSagemakerStudioUser(input: $input) {
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

export default createSagemakerStudioUser;
