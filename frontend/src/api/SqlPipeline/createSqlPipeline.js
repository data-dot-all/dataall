import { gql } from 'apollo-boost';

const createSqlPipeline = ({ input }) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation CreateSqlPipeline($input: NewSqlPipelineInput) {
      createSqlPipeline(input: $input) {
        sqlPipelineUri
        name
        label
        created
      }
    }
  `
});

export default createSqlPipeline;
