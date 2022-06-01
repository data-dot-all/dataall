import { gql } from 'apollo-boost';

const startDataProcessingPipeline = (DataPipelineUri) => ({
  variables: {
    DataPipelineUri
  },
  mutation: gql`
    mutation StartDataProcessingPipeline($DataPipelineUri: String!) {
      startDataProcessingPipeline(DataPipelineUri: $DataPipelineUri)
    }
  `
});

export default startDataProcessingPipeline;
