import { gql } from 'apollo-boost';

export const browseDataPipelineRepository = (input) => ({
  variables: {
    input
  },
  query: gql`
    query BrowseDataPipelineRepository($input: DataPipelineBrowseInput!) {
      browseDataPipelineRepository(input: $input)
    }
  `
});
