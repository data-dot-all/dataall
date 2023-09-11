import { gql } from 'apollo-boost';

export const updateDatasetTable = ({ tableUri, input }) => ({
  variables: {
    tableUri,
    input
  },
  mutation: gql`
    mutation UpdateDatasetTable(
      $tableUri: String!
      $input: ModifyDatasetTableInput!
    ) {
      updateDatasetTable(tableUri: $tableUri, input: $input) {
        tableUri
      }
    }
  `
});
