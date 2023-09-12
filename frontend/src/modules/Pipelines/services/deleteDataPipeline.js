import { gql } from 'apollo-boost';

export const deleteDataPipeline = ({ DataPipelineUri, deleteFromAWS }) => ({
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
