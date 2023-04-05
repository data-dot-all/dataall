import { gql } from 'apollo-boost';

export const getWorksheet = (worksheetUri) => ({
  variables: {
    worksheetUri
  },
  query: gql`
    query GetWorksheet($worksheetUri: String!) {
      getWorksheet(worksheetUri: $worksheetUri) {
        worksheetUri
        label
        description
        SamlAdminGroupName
        tags
        sqlBody
        chartConfig {
          dimensions {
            columnName
          }
          measures {
            columnName
            aggregationName
          }
        }
        owner
        created
        updated
        userRoleForWorksheet
        lastSavedQueryResult {
          AthenaQueryId
          ElapsedTimeInMs
          Error
          DataScannedInBytes
          Status
          columns {
            columnName
            typeName
          }
          rows {
            cells {
              value
              columnName
            }
          }
        }
      }
    }
  `
});
