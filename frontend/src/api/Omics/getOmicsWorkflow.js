import { gql } from 'apollo-boost';
// TODO: add output fields
const getOmicsWorkflow = (workflowUri) => ({
  variables: {
    workflowUri
  },
  query: gql`
    query getOmicsWorkflow($workflowUri: String!) {
      getOmicsWorkflow(workflowUri: $workflowUri) {
        workflowUri
        // TODO: add output fields
      }
    }
  `
});

export default getOmicsWorkflow;
