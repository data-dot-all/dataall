import { gql } from 'apollo-boost';

export const updateDataPipelineEnvironment = ({ input }) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation updateDataPipelineEnvironment(
      $input: NewDataPipelineEnvironmentInput!
    ) {
      updateDataPipelineEnvironment(input: $input) {
        envPipelineUri
        environmentUri
        environmentLabel
        pipelineUri
        pipelineLabel
        stage
        region
        AwsAccountId
        samlGroupName
      }
    }
  `
});
