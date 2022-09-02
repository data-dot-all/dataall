import { gql } from 'apollo-boost';

const listDataPipelineEnvironments = (filter) => ({
  variables: {
    filter
  },
  query: gql`
    query listDataPipelineEnvironments($filter: DataPipelineEnvironmentFilter) {
      listDataPipelineEnvironments(filter: $filter) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          envPipelineUri       
          environmentUri
          environmentLabel
          pipelineUri
          pipelineLabel
          stage
          region
          AwsAccountId
          SamlGroupName
        }
      }
    }
  `
});

export default listDataPipelineEnvironments;
