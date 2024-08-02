import { gql } from 'apollo-boost';

export const createRedshiftConnection = (input) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation createRedshiftConnection($input: CreateRedshiftConnectionInput) {
      createRedshiftConnection(input: $input) {
        connectionUri
      }
    }
  `
});
