import { gql } from 'apollo-boost';

const createDataPipelineEnvironment = ({ input }) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation createDataPipelineEnvironment($input: NewDataPipelineEnvironmentInput) {
      createDataPipelineEnvironment(input: $input) {
      }
    }
  `
});

export default createDataPipelineEnvironment;
