import { gql } from 'apollo-boost';

const deleteDataPipelineEnvironment = ({ envPipelineUri }) => ({
  variables: {
    envPipelineUri
  },
  mutation: gql`
    mutation deleteDataPipelineEnvironment(
      $envPipelineUri: String!
    ) {
      deleteDataPipelineEnvironment(
        envPipelineUri: $envPipelineUri
      )
    }
  `
});

export default deleteDataPipelineEnvironment;
