import { gql } from 'apollo-boost';

export const createWorksheetQueryResultDownloadUrl = ({
  fileFormat,
  environmentUri,
  athenaQueryId,
  worksheetUri
}) => ({
  variables: {
    fileFormat,
    environmentUri,
    athenaQueryId,
    worksheetUri
  },
  query: gql`
    mutation CreateWorksheetQueryResultDownloadUrl(
      $fileFormat: String!
      $environmentUri: String!
      $athenaQueryId: String!
      $worksheetUri: String!
    ) {
      createWorksheetQueryResultDownloadUrl(
        input: {
          fileFormat: $fileFormat
          environmentUri: $environmentUri
          athenaQueryId: $athenaQueryId
          worksheetUri: $worksheetUri
        }
      ) {
        downloadLink
        AthenaQueryId
        expiresIn
        fileFormat
        OutputLocation
      }
    }
  `
});


