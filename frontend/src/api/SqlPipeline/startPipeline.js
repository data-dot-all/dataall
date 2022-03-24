import { gql } from 'apollo-boost';

const startDataProcessingPipeline = (sqlPipelineUri) => ({
  variables: {
    sqlPipelineUri
  },
  mutation: gql`mutation StartDataProcessingPipeline(
            $sqlPipelineUri:String!
        ){
            startDataProcessingPipeline(sqlPipelineUri:$sqlPipelineUri)
        }`
});

export default startDataProcessingPipeline;
