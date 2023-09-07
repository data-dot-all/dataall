import { gql } from 'apollo-boost';
// TODO: review API output
export const listOmicsRuns = (filter) => ({
  variables: {
    filter
  },
  query: gql`
    query listOmicsRuns($filter: OmicsRunsFilter) {
      listOmicsRuns(filter: $filter) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          runUri
          name
          owner
          description
          label
          created
          tags
          // TODO: review this output
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
          stack {
            stack
            status
          }
        }
      }
    }
  `
});
