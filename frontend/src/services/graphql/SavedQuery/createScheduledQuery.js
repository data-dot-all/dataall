import { gql } from 'apollo-boost';

export const createScheduledQuery = (input) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation CreateScheduledQuery($input: NewScheduledQueryInput) {
      createScheduledQuery(input: $input) {
        scheduledQueryUri
        name
        label
        created
        description
        tags
      }
    }
  `
});
