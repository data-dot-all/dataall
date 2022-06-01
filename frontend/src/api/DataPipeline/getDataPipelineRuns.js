import { gql } from 'apollo-boost';

const getDataPipelineRuns = (DataPipelineUri) => ({
  variables: {
    DataPipelineUri
  },
  query: gql`
    query GetDataPipeline($DataPipelineUri: String!) {
      getDataPipeline(DataPipelineUri: $DataPipelineUri) {
        DataPipelineUri
        runs {
          Id
          JobName
          StartedOn
          CompletedOn
          JobRunState
          ErrorMessage
          ExecutionTime
        }
      }
    }
  `
});

export default getDataPipelineRuns;
