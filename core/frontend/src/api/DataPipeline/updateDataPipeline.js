import { gql } from 'apollo-boost';

const updateDataPipeline = ({ DataPipelineUri, input }) => ({
  variables: {
    DataPipelineUri,
    input
  },
  mutation: gql`
    mutation UpdateDataPipeline(
      $input: UpdateDataPipelineInput
      $DataPipelineUri: String!
    ) {
      updateDataPipeline(DataPipelineUri: $DataPipelineUri, input: $input) {
        DataPipelineUri
        name
        label
        created
        tags
      }
    }
  `
});

export default updateDataPipeline;
