import { gql } from 'apollo-boost';

const listDataPipelineBranches = (DataPipelineUri) => ({
  variables: {
    DataPipelineUri
  },
  query: gql`
    query ListDataPipelineBranches($DataPipelineUri: String!) {
      listDataPipelineBranches(DataPipelineUri: $DataPipelineUri)
    }
  `
});

export default listDataPipelineBranches;
