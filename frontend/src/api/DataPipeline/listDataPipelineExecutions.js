import { gql } from 'apollo-boost';

const listDataPipelineExecutions = ({ DataPipelineUri, stage }) => ({
  variables: {
    DataPipelineUri,
    stage
  },
  query: gql`
    query ListDataPipelineExecutions($DataPipelineUri: String!, $stage: String) {
      listDataPipelineExecutions(
        DataPipelineUri: $DataPipelineUri
        stage: $stage
      ) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          executionArn
          stateMachineArn
          name
          status
          startDate
          stopDate
        }
      }
    }
  `
});

export default listDataPipelineExecutions;
