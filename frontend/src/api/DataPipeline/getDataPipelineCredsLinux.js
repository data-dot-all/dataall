import { gql } from 'apollo-boost';

export const getDataPipelineCredsLinux = (DataPipelineUri) => ({
  variables: {
    DataPipelineUri
  },
  query: gql`
    query GetDataPipelineCredsLinux($DataPipelineUri: String!) {
      getDataPipelineCredsLinux(DataPipelineUri: $DataPipelineUri)
    }
  `
});
