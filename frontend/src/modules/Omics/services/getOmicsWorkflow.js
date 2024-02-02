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
        id
        name
        description
        parameterTemplate
        type
      }
    }
  `
});
