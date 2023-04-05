import { gql } from 'apollo-boost';

export const startDatasetProfilingRun = ({ input }) => ({
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
