import { gql } from 'apollo-boost';
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
          id
          name
          label
          workflowUri
          description
          type
          parameterTemplate
        }
      }
    }
  `
});
