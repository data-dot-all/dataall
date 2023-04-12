import { gql } from 'apollo-boost';

export const deployScheduledQuery = (scheduledQueryUri) => ({
  variables: {
    scheduledQueryUri
  },
  mutation: gql`
    mutation DeployScheduledQuery($scheduledQueryUri: String!) {
      deployScheduledQuery(scheduledQueryUri: $scheduledQueryUri)
    }
  `
});
