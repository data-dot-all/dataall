import { gql } from 'apollo-boost';

export const createWorksheetQueryResultDownloadUrl = (input) => ({
  variables: {
    input
  },
  query: gql`
    mutation CreateWorksheetQueryResultDownloadUrl(
      $input: WorksheetQueryResultDownloadUrlInput!
    ) {
      createWorksheetQueryResultDownloadUrl(
        input: $input
      ) {
        downloadLink
        AthenaQueryId
        expiresIn
        fileFormat
        outputLocation
      }
    }
  `
});
