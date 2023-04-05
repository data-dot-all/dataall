import { gql } from 'apollo-boost';

export const deleteWorksheet = (worksheetUri) => ({
  variables: {
    worksheetUri
  },
  mutation: gql`
    mutation deleteWorksheet($worksheetUri: String!) {
      deleteWorksheet(worksheetUri: $worksheetUri)
    }
  `
});
