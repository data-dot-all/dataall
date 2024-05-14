import { gql } from 'apollo-boost';
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
          workflowUri
          name
          owner
          SamlAdminGroupName
          outputDatasetUri
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
            label
            name
            workflowUri
            id
            description
            parameterTemplate
            type
          }
          status {
            status
            statusMessage
          }
        }
      }
    }
  `
});
