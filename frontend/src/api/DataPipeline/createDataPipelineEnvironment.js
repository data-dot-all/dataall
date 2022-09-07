import { gql } from 'apollo-boost';

const createDataPipelineEnvironment = ({ input }) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation createDataPipelineEnvironment($input: NewDataPipelineEnvironmentInput) {
      createDataPipelineEnvironment(input: $input) {
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

export default createDataPipelineEnvironment;
