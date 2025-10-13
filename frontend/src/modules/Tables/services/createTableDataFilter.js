import { gql } from 'apollo-boost';

export const createTableDataFilter = ({ tableUri, input }) => ({
  variables: {
    tableUri,
    input
  },
  mutation: gql`
    mutation createTableDataFilter(
      $tableUri: String!
      $input: NewTableDataFilterInput!
    ) {
      createTableDataFilter(tableUri: $tableUri, input: $input) {
        filterUri
      }
    }
  `
});
