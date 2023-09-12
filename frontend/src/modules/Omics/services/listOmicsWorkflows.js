import { gql } from 'apollo-boost';

// TODO: review API output
export const listOmicsWorkflows = (filter) => ({
  variables: {
    filter
  },
  query: gql`
    query listOmicsWorkflows($filter: OmicsFilter) {
      listOmicsWorkflows(filter: $filter) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          arn
          name
          id
          description
          status
          type
          parameterTemplate
        }
      }
    }
  `
});
