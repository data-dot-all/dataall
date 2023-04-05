import { gql } from 'apollo-boost';

export const startProfilingJob = (tableUri) => ({
  variables: {
    tableUri
  },
  mutation: gql`
    mutation StartProfilingJob($tableUri: String!) {
      startProfilingJob(tableUri: $tableUri) {
        jobUri
      }
    }
  `
});
