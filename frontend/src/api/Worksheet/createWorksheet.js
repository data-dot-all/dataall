import { gql } from 'apollo-boost';

export const createWorksheet = (input) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation CreateWorksheet($input: NewWorksheetInput) {
      createWorksheet(input: $input) {
        worksheetUri
        label
        created
      }
    }
  `
});
