import { gql } from 'apollo-boost';

const getSqlPipelineCredsLinux = (sqlPipelineUri) => ({
  variables: {
    sqlPipelineUri
  },
  query: gql`
    query GetSqlPipelineCredsLinux($sqlPipelineUri: String!) {
      getSqlPipelineCredsLinux(sqlPipelineUri: $sqlPipelineUri)
    }
  `
});

export default getSqlPipelineCredsLinux;
