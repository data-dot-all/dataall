import { gql } from 'apollo-boost';

const createWorksheet = (input) => ({
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

export default createWorksheet;
