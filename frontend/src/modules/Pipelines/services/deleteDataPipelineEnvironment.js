import { gql } from 'apollo-boost';

export const deleteDataPipelineEnvironment = ({ envPipelineUri }) => ({
  variables: {
    envPipelineUri
  },
  mutation: gql`
    mutation deleteDataPipelineEnvironment($envPipelineUri: String!) {
      deleteDataPipelineEnvironment(envPipelineUri: $envPipelineUri)
    }
  `
});
