import { gql } from 'apollo-boost';

const deleteDataPipelineEnvironment = ({ dataPipelineUri, environmentUri, stage }) => ({
  variables: {
    dataPipelineUri,
    environmentUri,
    stage  
  },
  mutation: gql`
    mutation deleteDataPipelineEnvironment(
      $dataPipelineUri: String!
      $environmentUri: String!
      $stage: String!
    ) {
      deleteDataPipelineEnvironment(
        dataPipelineUri: $dataPipelineUri
        environmentUri: $environmentUri
        stage: $stage
      )
    }
  `
});

export default deleteDataPipelineEnvironment;
