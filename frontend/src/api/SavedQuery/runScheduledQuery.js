import { gql } from 'apollo-boost';

const runScheduledQuery = (scheduledQueryUri) => ({
  variables: {
    scheduledQueryUri
  },
  mutation: gql`
    mutation RunScheduledQuery($scheduledQueryUri: String!) {
      runScheduledQuery(scheduledQueryUri: $scheduledQueryUri)
    }
  `
});

export default runScheduledQuery;
