import { gql } from 'apollo-boost';

const updatePipelineStack = (DataPipelineUri) => ({
  variables: { DataPipelineUri },
  mutation: gql`
    mutation updatePipelineStack($DataPipelineUri: String!) {
      updatePipelineStack(DataPipelineUri: $DataPipelineUri)
    }
  `
});

export default updatePipelineStack;
