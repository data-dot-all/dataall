import { gql } from 'apollo-boost';

const createDataPipeline = ({ input }) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation CreateDataPipeline($input: NewDataPipelineInput) {
      createDataPipeline(input: $input) {
        DataPipelineUri
        name
        label
        created
      }
    }
  `
});

export default createDataPipeline;
