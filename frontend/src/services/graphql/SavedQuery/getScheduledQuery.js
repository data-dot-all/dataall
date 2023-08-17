import { gql } from 'apollo-boost';

export const getScheduledQuery = (scheduledQueryUri) => ({
  variables: {
    scheduledQueryUri
  },
  query: gql`
    query GetScheduledQuery($scheduledQueryUri: String!) {
      getScheduledQuery(scheduledQueryUri: $scheduledQueryUri) {
        scheduledQueryUri
        name
        label
        cronexpr
        description
        owner
        created
        description
        queries {
          count
          page
          pages
          nodes {
            savedQueryUri
            sqlBody
            description
            label
            name
            queryOrder
          }
        }
      }
    }
  `
});
