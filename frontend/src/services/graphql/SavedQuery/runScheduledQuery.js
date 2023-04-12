import { gql } from 'apollo-boost';

export const runScheduledQuery = (scheduledQueryUri) => ({
  variables: {
    scheduledQueryUri
  },
  mutation: gql`
    mutation RunScheduledQuery($scheduledQueryUri: String!) {
      runScheduledQuery(scheduledQueryUri: $scheduledQueryUri)
    }
  `
});
