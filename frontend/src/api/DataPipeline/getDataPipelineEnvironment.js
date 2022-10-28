import { gql } from 'apollo-boost';

const getDataPipelineEnvironment = (envPipelineUri) => ({
  variables: {
    envPipelineUri
  },
  query: gql`
    query getDataPipelineEnvironment($envPipelineUri: String!) {
      getDataPipelineEnvironment(envPipelineUri: $envPipelineUri) {
        envPipelineUri       
        environmentUri
        environmentLabel
        pipelineUri
        pipelineLabel
        stage
        region
        AwsAccountId
        SamlGroupName
      }
    }
  `
});

export default getDataPipelineEnvironment;
