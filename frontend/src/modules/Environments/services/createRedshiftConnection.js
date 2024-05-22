import { gql } from 'apollo-boost';

export const createRedshiftConnection = (input) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation createRedshiftConnection($input: NewRedshiftConnection) {
      createRedshiftConnection(input: $input) {
        connectionUri
      }
    }
  `
});
