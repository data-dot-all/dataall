import { gql } from 'apollo-boost';

export const listWorksheetShares = ({ worksheetUri, filter }) => ({
  variables: {
    worksheetUri,
    filter
  },
  query: gql`
    query GetWorksheet($worksheetUri: String!, $filter: WorksheetFilter) {
      getWorksheet(worksheetUri: $worksheetUri) {
        shares(filter: $filter) {
          count
          page
          pages
          hasNext
          hasPrevious
          nodes {
            worksheetShareUri
            principalId
            principalType
          }
        }
      }
    }
  `
});
