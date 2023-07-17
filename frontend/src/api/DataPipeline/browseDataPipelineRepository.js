import { gql } from 'apollo-boost';

const browseDataPipelineRepository = (input) => ({
  variables: {
    input
  },
  query: gql`
    query BrowseDataPipelineRepository($input: DataPipelineBrowseInput!) {
      browseDataPipelineRepository(input: $input)
    }
  `
});

export default browseDataPipelineRepository;
