import { gql } from 'apollo-boost';

export const publishDatasetTableUpdate = ({ tableUri }) => ({
  variables: {
    tableUri
  },
  mutation: gql`
    mutation publishDatasetTableUpdate($tableUri: String!) {
      publishDatasetTableUpdate(tableUri: $tableUri)
    }
  `
});
