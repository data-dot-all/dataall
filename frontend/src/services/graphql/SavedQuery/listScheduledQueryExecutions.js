import { gql } from 'apollo-boost';

export const listScheduledQueryExecutions = (scheduledQueryUri) => ({
  variables: {
    scheduledQueryUri
  },
  query: gql`
    query ListScheduledQueryExecutions($scheduledQueryUri: String!) {
      listScheduledQueryExecutions(scheduledQueryUri: $scheduledQueryUri) {
        executionArn
        status
        startDate
        stopDate
      }
    }
  `
});
