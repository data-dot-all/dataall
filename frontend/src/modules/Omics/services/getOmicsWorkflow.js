import { gql } from 'apollo-boost';
// TODO: add output fields
export const getOmicsWorkflow = (workflowId) => ({
  variables: {
    workflowId
  },
  query: gql`
    query getOmicsWorkflow($workflowId: String!) {
      getOmicsWorkflow(workflowId: $workflowId) {
        id
        name
        description
        parameterTemplate
        status
        type
      }
    }
  `
});
