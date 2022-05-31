import { gql } from 'apollo-boost';

const deleteSqlPipeline = ({ sqlPipelineUri, deleteFromAWS }) => ({
  variables: {
    sqlPipelineUri,
    deleteFromAWS
  },
  mutation: gql`
    mutation deleteSqlPipeline(
      $sqlPipelineUri: String!
      $deleteFromAWS: Boolean
    ) {
      deleteSqlPipeline(
        sqlPipelineUri: $sqlPipelineUri
        deleteFromAWS: $deleteFromAWS
      )
    }
  `
});

export default deleteSqlPipeline;
