import { gql } from 'apollo-boost';

const getSqlPipelineBuilds = (sqlPipelineUri) => ({
  variables: {
    sqlPipelineUri
  },
  query: gql`
    query GetSqlPipeline($sqlPipelineUri: String!) {
      getSqlPipeline(sqlPipelineUri: $sqlPipelineUri) {
        sqlPipelineUri
        builds {
          pipelineExecutionId
          status
          startTime
          lastUpdateTime
        }
      }
    }
  `
});

export default getSqlPipelineBuilds;
