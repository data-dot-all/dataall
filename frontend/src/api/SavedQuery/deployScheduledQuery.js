import { gql } from 'apollo-boost';

const deployScheduledQuery = (scheduledQueryUri) => ({
  variables: {
    scheduledQueryUri
  },
  mutation: gql`
    mutation DeployScheduledQuery($scheduledQueryUri: String!) {
      deployScheduledQuery(scheduledQueryUri: $scheduledQueryUri)
    }
  `
});

export default deployScheduledQuery;
