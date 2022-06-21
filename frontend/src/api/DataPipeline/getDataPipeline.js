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
        devStages
        devStrategy
        inputDatasetUri
        outputDatasetUri
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
        runs {
          Id
          StartedOn
          JobRunState
        }
      }
    }
  `
});

export default getDataPipeline;
