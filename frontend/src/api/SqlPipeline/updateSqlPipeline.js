import { gql } from 'apollo-boost';

const updateSqlPipeline = ({ sqlPipelineUri, input }) => ({
  variables: {
    sqlPipelineUri,
    input
  },
  mutation: gql`mutation UpdateSqlPipeline(
            $input:UpdateSqlPipelineInput,
            $sqlPipelineUri:String!
        ){
            updateSqlPipeline(sqlPipelineUri:$sqlPipelineUri,input:$input){
                sqlPipelineUri
                name
                label
                created
                tags
            }
        }`
});

export default updateSqlPipeline;
