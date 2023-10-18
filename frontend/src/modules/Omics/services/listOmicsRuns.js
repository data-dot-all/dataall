import { gql } from 'apollo-boost';
// TODO: review API output
export const listOmicsRuns = (filter) => ({
  variables: {
    filter
  },
  query: gql`
    query listOmicsRuns($filter: OmicsFilter) {
      listOmicsRuns(filter: $filter) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          runUri
          workflowId
          name
          owner
          SamlAdminGroupName
          outputUri
          description
          label
          created
          tags
          environment {
            label
            name
            environmentUri
            AwsAccountId
            region
            SamlGroupName
          }
          organization {
            label
            name
            organizationUri
          }
          workflow {
            id
            name
            description
            parameterTemplate
            status
            type
          }
          status {
            arn
            id
            status
            runId
            roleArn
            statusMessage
            creationTime
            startTime
            stopTime
          }
        }
      }
    }
  `
});
