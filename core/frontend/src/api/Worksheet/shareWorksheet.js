import { gql } from 'apollo-boost';

const shareWorksheet = ({ worksheetUri, input }) => ({
  variables: {
    worksheetUri,
    input
  },
  mutation: gql`
    mutation ShareWorksheet(
      $worksheetUri: String!
      $input: WorksheetShareInput!
    ) {
      shareWorksheet(worksheetUri: $worksheetUri, input: $input) {
        worksheetShareUri
      }
    }
  `
});

export default shareWorksheet;
