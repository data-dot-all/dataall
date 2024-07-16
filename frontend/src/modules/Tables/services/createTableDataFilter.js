import { gql } from 'apollo-boost';

export const createTableDataFilter = (input) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation createTableDataFilter($input: NewDataFilterInput) {
      createTableDataFilter(input: $input) {
        filterUri
      }
    }
  `
});
