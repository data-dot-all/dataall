import { gql } from 'apollo-boost';

const startDatasetProfilingRun = ({ input }) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation startDatasetProfilingRun($input: StartDatasetProfilingRunInput!) {
      startDatasetProfilingRun(input: $input) {
        profilingRunUri
      }
    }
  `
});

export default startDatasetProfilingRun;
