import { gql } from 'apollo-boost';

export const runAthenaSqlQuery = ({
  sqlQuery,
  environmentUri,
  worksheetUri
}) => ({
  variables: {
    sqlQuery,
    environmentUri,
    worksheetUri
  },
  query: gql`
    query runAthenaSqlQuery(
      $environmentUri: String!
      $worksheetUri: String!
      $sqlQuery: String!
    ) {
      runAthenaSqlQuery(
        environmentUri: $environmentUri
        worksheetUri: $worksheetUri
        sqlQuery: $sqlQuery
      ) {
        rows {
          cells {
            columnName
            typeName
            value
          }
        }
        columns {
          columnName
          typeName
        }
      }
    }
  `
});
