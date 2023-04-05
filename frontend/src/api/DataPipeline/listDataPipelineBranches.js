import { gql } from 'apollo-boost';

export const listDataPipelineBranches = (DataPipelineUri) => ({
  variables: {
    DataPipelineUri
  },
  query: gql`
    query ListDataPipelineBranches($DataPipelineUri: String!) {
      listDataPipelineBranches(DataPipelineUri: $DataPipelineUri)
    }
  `
});
