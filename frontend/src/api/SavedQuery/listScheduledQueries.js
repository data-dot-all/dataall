import { gql } from 'apollo-boost';

export const listScheduledQueries = (filter) => ({
  variables: {
    filter
  },
  query: gql`
    query ListScheduledQueries($filter: ScheduledQueryFilter) {
      listScheduledQueries(filter: $filter) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          scheduledQueryUri
          name
          owner
          description
          label
          created
          tags
          environment {
            AwsAccountId
            region
            name
            label
          }
          organization {
            organizationUri
            name
          }
        }
      }
    }
  `
});
