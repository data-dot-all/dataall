import { gql } from 'apollo-boost';

export const deleteDatasetTable = ({ tableUri }) => ({
  variables: {
    tableUri
  },
  mutation: gql`
    mutation deleteDatasetTable($tableUri: String!) {
      deleteDatasetTable(tableUri: $tableUri)
    }
  `
});
