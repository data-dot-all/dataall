import { gql } from 'apollo-boost';

export const listDatasetTableProfilingRuns = (tableUri) => ({
  variables: {
    tableUri
  },
  query: gql`
    query listDatasetTableProfilingRuns($tableUri: String!) {
      listDatasetTableProfilingRuns(tableUri: $tableUri) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          profilingRunUri
          GlueJobRunId
          GlueTableName
          results
          created
          status
        }
      }
    }
  `
});
