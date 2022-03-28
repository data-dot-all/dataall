import { gql } from 'apollo-boost';

const getSqlPipelineRuns = (sqlPipelineUri) => ({
  variables: {
    sqlPipelineUri
  },
  query: gql`
    query GetSqlPipeline($sqlPipelineUri: String!) {
      getSqlPipeline(sqlPipelineUri: $sqlPipelineUri) {
        sqlPipelineUri
        runs {
          Id
          JobName
          StartedOn
          CompletedOn
          JobRunState
          ErrorMessage
          ExecutionTime
        }
      }
    }
  `
});

export default getSqlPipelineRuns;
