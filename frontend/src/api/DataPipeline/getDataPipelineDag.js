import { gql } from 'apollo-boost';

export const getDataPipelineDag = (DataPipelineUri) => ({
  variables: {
    DataPipelineUri
  },
  query: gql`
    query GetDataPipelineDag($DataPipelineUri: String!) {
      getDataPipelineDag(DataPipelineUri: $DataPipelineUri)
    }
  `
});
