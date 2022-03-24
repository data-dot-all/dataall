import { gql } from 'apollo-boost';

const updatePipelineStack = (sqlPipelineUri) => ({
  variables: { sqlPipelineUri },
  mutation: gql`mutation updatePipelineStack(
            $sqlPipelineUri:String!
        ){
            updatePipelineStack(
                sqlPipelineUri:$sqlPipelineUri
            )
        }`
});

export default updatePipelineStack;
