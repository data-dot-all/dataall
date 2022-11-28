import { gql } from 'apollo-boost';

const deleteDataPipeline = ({ DataPipelineUri, deleteFromAWS }) => ({
  variables: {
    DataPipelineUri,
    deleteFromAWS
  },
  mutation: gql`
    mutation deleteDataPipeline(
      $DataPipelineUri: String!
      $deleteFromAWS: Boolean
    ) {
      deleteDataPipeline(
        DataPipelineUri: $DataPipelineUri
        deleteFromAWS: $deleteFromAWS
      )
    }
  `
});

export default deleteDataPipeline;
