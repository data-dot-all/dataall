import { gql } from 'apollo-boost';

const getSqlPipelineFileContent = (input) => ({
  variables: {
    input
  },
  query: gql`
            query getSqlPipelineFileContent($input:SqlPipelineFileContentInput!){
                getSqlPipelineFileContent(input:$input)
            }
        `
});

export default getSqlPipelineFileContent;
