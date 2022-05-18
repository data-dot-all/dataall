import { gql } from 'apollo-boost';

const getDataPipelineBuilds = (DataPipelineUri) => ({
  variables: {
    DataPipelineUri
  },
  query: gql`
    query GetDataPipeline($DataPipelineUri: String!) {
      getDataPipeline(DataPipelineUri: $DataPipelineUri) {
        DataPipelineUri
        builds {
          pipelineExecutionId
          status
          startTime
          lastUpdateTime
        }
      }
    }
  `
});

export default getDataPipelineBuilds;
