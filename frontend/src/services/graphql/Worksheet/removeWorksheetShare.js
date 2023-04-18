import { gql } from 'apollo-boost';

export const removeWorksheetShare = (worksheetShareUri) => ({
  variables: {
    worksheetShareUri
  },
  mutation: gql`
    mutation RemoveWorksheetShare($worksheetShareUri: String!) {
      removeWorksheetShare(worksheetShareUri: $worksheetShareUri)
    }
  `
});
