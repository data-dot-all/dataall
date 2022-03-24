import { gql } from 'apollo-boost';

const browseSqlPipelineRepository = (input) => ({
  variables: {
    input
  },
  query: gql`
            query BrowseSqlPipelineRepository($input:SqlPipelineBrowseInput!){
                browseSqlPipelineRepository(input:$input)
            }
        `
});

export default browseSqlPipelineRepository;
