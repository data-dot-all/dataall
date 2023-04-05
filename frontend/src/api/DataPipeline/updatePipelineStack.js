import { gql } from 'apollo-boost';

export const updatePipelineStack = (DataPipelineUri) => ({
  variables: { DataPipelineUri },
  mutation: gql`
    mutation updatePipelineStack($DataPipelineUri: String!) {
      updatePipelineStack(DataPipelineUri: $DataPipelineUri)
    }
  `
});
