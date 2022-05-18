import { gql } from 'apollo-boost';

const getDataPipelineDag = (DataPipelineUri) => ({
  variables: {
    DataPipelineUri
  },
  query: gql`
    query GetDataPipelineDag($DataPipelineUri: String!) {
      getDataPipelineDag(DataPipelineUri: $DataPipelineUri)
    }
  `
});

export default getDataPipelineDag;
