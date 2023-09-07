import { gql } from 'apollo-boost';
// TODO: add output fields
export const getOmicsWorkflow = (workflowUri) => ({
  variables: {
    workflowUri
  },
  query: gql`
    query getOmicsWorkflow($workflowUri: String!) {
      getOmicsWorkflow(workflowUri: $workflowUri) {
        workflowUri
        // TODO: add output fields
        parameterTemplate
      }
    }
  `
});
