import { gql } from 'apollo-boost';

// TODO: review API output
const listOmicsWorkflows = (filter) => ({
  variables: {
    filter
  },
  query: gql`
    query listOmicsWorkflows($filter: OmicsWorkflowsFilter) {
      listOmicsWorkflows(filter: $filter) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          workflowUri
          name
          owner
          description
          label
          created
          tags
          // TODO: review this output
        }
      }
    }
  `
});

export default listOmicsWorkflows;

