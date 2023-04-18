import { gql } from 'apollo-boost';

export const getDataPipelineFileContent = (input) => ({
  variables: {
    input
  },
  query: gql`
    query getDataPipelineFileContent($input: DataPipelineFileContentInput!) {
      getDataPipelineFileContent(input: $input)
    }
  `
});
