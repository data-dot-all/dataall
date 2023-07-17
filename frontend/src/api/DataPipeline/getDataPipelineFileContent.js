import { gql } from 'apollo-boost';

const getDataPipelineFileContent = (input) => ({
  variables: {
    input
  },
  query: gql`
    query getDataPipelineFileContent($input: DataPipelineFileContentInput!) {
      getDataPipelineFileContent(input: $input)
    }
  `
});

export default getDataPipelineFileContent;
