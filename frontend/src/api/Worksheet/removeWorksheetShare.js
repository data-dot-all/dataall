import { gql } from 'apollo-boost';

const removeWorksheetShare = (worksheetShareUri) => ({
  variables: {
    worksheetShareUri
  },
  mutation: gql`
    mutation RemoveWorksheetShare($worksheetShareUri: String!) {
      removeWorksheetShare(worksheetShareUri: $worksheetShareUri)
    }
  `
});

export default removeWorksheetShare;
