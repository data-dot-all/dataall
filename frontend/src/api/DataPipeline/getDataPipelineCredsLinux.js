import { gql } from 'apollo-boost';

const getDataPipelineCredsLinux = (DataPipelineUri) => ({
  variables: {
    DataPipelineUri
  },
  query: gql`
    query GetDataPipelineCredsLinux($DataPipelineUri: String!) {
      getDataPipelineCredsLinux(DataPipelineUri: $DataPipelineUri)
    }
  `
});

export default getDataPipelineCredsLinux;
