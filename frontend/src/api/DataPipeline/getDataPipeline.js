import { gql } from 'apollo-boost';

const getDataPipeline = (DataPipelineUri) => ({
  variables: {
    DataPipelineUri
  },
  query: gql`
    query GetDataPipeline($DataPipelineUri: String!) {
      getDataPipeline(DataPipelineUri: $DataPipelineUri) {
        DataPipelineUri
        name
        owner
        SamlGroupName
        description
        label
        created
        userRoleForPipeline
        tags
        repo
        cloneUrlHttp
        devStrategy
        template
        environment {
          environmentUri
          AwsAccountId
          region
          label
        }
        organization {
          organizationUri
          label
          name
        }
        developmentEnvironments {
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
            order
            region
            AwsAccountId
            samlGroupName
          }
        }
        stack {
          stack
          status
          stackUri
          targetUri
          accountid
          region
          stackid
          link
          outputs
          resources
        }
      }
    }
  `
});

export default getDataPipeline;
