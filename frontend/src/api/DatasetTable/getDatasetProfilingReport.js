import { gql } from 'apollo-boost';

export const getDatasetTableProfilingReport = (jobUri) => ({
  variables: {
    jobUri
  },
  query: gql`
    query getDatasetTableProfilingReport($jobUri: String!) {
      getDatasetTableProfilingReport(jobUri: $jobUri)
    }
  `
});
