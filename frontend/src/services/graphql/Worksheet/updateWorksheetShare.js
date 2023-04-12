import { gql } from 'apollo-boost';

export const updateWorksheetShare = ({ worksheetShareUri, canEdit }) => ({
  variables: {
    worksheetShareUri,
    canEdit
  },
  mutation: gql`
    mutation RemoveWorksheetShare(
      $worksheetShareUri: String!
      $canEdit: Boolean
    ) {
      updateWorksheetShare(
        worksheetShareUri: $worksheetShareUri
        canEdit: $canEdit
      ) {
        worksheetShareUri
        canEdit
      }
    }
  `
});
